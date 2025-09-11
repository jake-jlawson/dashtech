





# Issues & Issue Context

## Notes
An issue will be defined as a current ongoing problem with the vehicle which is either currently being diagnosed, fixed, etc. A user can create a new issue by running the diagnostics. The comms agent can create a new issue also if it detects problems with the vehicle.
- An issue will provide IssueContext on the backend which will provide the environment/context for the agents to run. This will store data/state such as a ranking / probabilities of the most likely issues, the current issue being explore (if there is one), a log of all the actions taken and tests run, etc.
- IssueContext will also provide functionality for converting all of this data to json or another document to save on the local filesystem. 
- There should be a route for creating a new issue. This route should create a websocket connection between the client and the backend for as long as the issue is opened, and only close it once that issue has resolved or closed. 

## API / Websocket
- Request is made to create a new issue.
- Check is run on whether there is already an active issue.
- If there is, the server accepts the socket, sends a rejection event explaining there is already an active issue, then closes the connection with WebSocket close code 1008 (policy violation).
- If not, it uses IssueManager to create a new issue, and set up the issue/connection.

## Class Design
Design allows us to unit test each and separates concern (providing logic vs providing the connection).

**IssueManager**: Handles the orchestration, lifecycle and networking for the IssueContext. It allows IssueContext to be setup and connected to the frontend. 
- IssueManager (lifecycle/orchestration):
  - Enforces single active issue (for now): `create_or_get()`, optional `force_new()`
  - Tracks per-issue WebSocket connections: `add_connection()`, `remove_connection()`
  - Broadcasts events to all clients of an issue: `broadcast()`
  - Closes lifecycle: `close_issue()` emits `issue.closed`, then closes sockets
  - Holds concurrency lock(s) to guard create/close transitions.

**IssueContext**: Provides logic, environment for agents to run in, etc. (probabilities, current hypothesis, logs, actions, inbound queue, persistence helpers, access to shared resources like LLMClient).
- Per-issue state and resources for agents to run:
    - `id`, `created_at`, `status`
    - `probabilities`, `current_hypothesis`
    - `actions[]`, `logs[]`
    - `queue` (async inbound work from clients/WS)
    - `connections` (sockets attached to this issue)
  - Methods: `to_summary()`, and future helpers for logging, persistence, and serialization.



## Strict create-only WebSocket policy

- Route: `GET ws://<host>/issue/create`
  - Behavior:
    - If no active issue exists: create a new `IssueContext`, send `{ type: "issue.created", issueId, data: <summary> }`, keep socket open for lifetime of the issue.
    - If an active issue exists: send `{ type: "issue.create_rejected", reason: "active_issue_exists", issueId: <currentId> }`, then close with code `1008`.
  - Rationale: keep `/issue/create` semantics unambiguous (create-or-fail), avoid accidental fan-out or dual semantics (create vs attach).

### Attach route (recommended)

- Route: `GET ws://<host>/issue/attach?issueId=<uuid>` (or `ws://<host>/issue/{issueId}/attach`)
  - If the issue is open: attach the socket, send `{ type: "issue.attached", issueId, data: <summary> }`.
  - If not found/closed: send `{ type: "issue.attach_rejected", reason: "not_found_or_closed", issueId }`, then close with `1008`.

### Error codes and payloads

- Close codes:
  - `1008` Policy Violation: used for rejecting create/attach when it violates current state.
  - `1013` Try Again Later: optional alternative if you want a softer signal “busy, retry later”.
- Rejection payload examples (sent before closing):
  - Create rejected: `{ type: "issue.create_rejected", reason: "active_issue_exists", issueId: <currentId> }`
  - Attach rejected: `{ type: "issue.attach_rejected", reason: "not_found_or_closed", issueId }`

### Reconnection & single-connection policy

- Reconnection: clients should reconnect to `issue/attach` with the known `issueId` after transient network issues.
- Single-connection-per-client (optional): require `clientId` on connect; if a new socket arrives with the same `clientId`, either:
  - Replace the old socket (close old with `1000` Normal Closure), or
  - Reject the new one with `1008` to enforce a strict single-connection policy.

### Heartbeats & reconnect hints

- Server should send periodic pings (or ping frames) to detect dead connections and clean up.
- On create rejection, include `issueId` and a hint to call `/issue/attach`.
- Consider `GET /issue/current` on app start to decide create vs attach.

### Auto-close policy

- If an issue has no attached sockets for N seconds/minutes, auto-close it to free resources.
- Emit `issue.closed` with reason `idle_timeout` before closing.

### Pros/cons of strict create-only

- Pros:
  - Clear API semantics; `/issue/create` never multiplexes concerns.
  - Easier to reason about client behavior and server invariants.
  - Avoids accidental multiple sockets per client.
- Cons:
  - Requires an additional attach route for reconnection and multi-client viewers.
  - Frontend must branch: create vs attach.

### Minimal WS handler behavior

- On `/issue/create` when an issue exists:
  - Accept socket, send `issue.create_rejected` with `issueId` of the active issue for UX guidance, then close `1008`.
- On `/issue/attach` when issue not found/closed:
  - Accept socket, send `issue.attach_rejected`, then close `1008`.







