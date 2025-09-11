from typing import Any, Dict, List, Set, Optional, Tuple, Union
from enum import Enum
import uuid, datetime, asyncio
from fastapi import WebSocket
from core.agents.diagnostics import LLMDiagnosticsAgent, DiagnosisProbability, Test
from core.agents.communications import CommunicationsAgent
from core.llm import LLMClient
from core.schemas import InboundMessage


class IssueProgress(Enum):
    ACTIVE = "active"
    CLOSING = "closing"
    CLOSED = "closed"


class IssueContext:
    def __init__(self, llm_client: LLMClient):
        self.id: str = str(uuid.uuid4())
        self.created_at: str = datetime.datetime.utcnow().isoformat()
        self.progress: IssueProgress = IssueProgress.ACTIVE

        # Event loop / queue
        self._q: asyncio.Queue[Dict[str, Any]] = asyncio.Queue()
        self._state_lock: asyncio.Lock = asyncio.Lock()
        self._result_event = asyncio.Event()
        self._seen_event_ids: Set[str] = set()

        self._handlers = self.register_handlers()




        # Manage connection
        self.connection: Optional[WebSocket] = None
        self._send_lock: asyncio.Lock = asyncio.Lock()


        # Manage agents & agent loop
        self.issue_params = { # parameters for the issue
            "probability_threshold": 0.9,
        }
        self.run_status: "pending" | "diagnostics" | "maintenance" | "resolved" = "pending"

        # Diagnostics Attributes
        self.diagnostics_agent = LLMDiagnosticsAgent(llm_client)
        self.active_diagnosis: DiagnosisProbability | None = None # stores the current diagnosis if one is set (none if still diagnosing)
        self.diagnosis_probabilities: List[DiagnosisProbability] = [] # stores the list of diagnosis probabilities
        self.tests_log: List[Test] = [] # stores ordered list/history of tests run

        # Communications Attributes
        self.communications_agent = CommunicationsAgent(llm_client, self.id)


    async def _run_issue_loop(self) -> None:
        """
        Run the issue loop.
        """
        try:
            while self.progress == IssueProgress.ACTIVE:
                if self.run_status == "diagnostics":
                    # Wait until we have at least one test and that test has a result
                    if len(self.tests_log) == 0:
                        # Nothing to do yet; yield so other tasks can run
                        await asyncio.sleep(0.05)
                        continue

                    if self.tests_log[-1].get("result") is None:
                        # Waiting for the most recent test result; yield control
                        await asyncio.sleep(0.05)
                        continue

                    # Run the diagnostics agent to update probabilities and obtain next test
                    self.diagnosis_probabilities, next_test = await self.diagnostics_agent.run(
                        self.diagnosis_probabilities,
                        self.tests_log,
                    )
                    print(f"Probabilities Updated: {self.diagnosis_probabilities}", flush=True)
                    print(f"Next Test: {next_test}", flush=True)

                    # Monitor probabilities to see if any are above the probability threshold
                    for potential_diagnosis in self.diagnosis_probabilities:
                        if potential_diagnosis.get("probability") > self.issue_params.get("probability_threshold"):
                            self.active_diagnosis = potential_diagnosis
                            self.run_status = "maintenance"
                            break

                    # Prepare the next test
                    self.tests_log.append(next_test)  # add the next test to the tests_log
                    _ = await self.communications_agent.communicate_test(next_test)  # send the next test to the user

                elif self.run_status == "maintenance":
                    # Placeholder: implement maintenance behavior; yield meanwhile
                    await asyncio.sleep(0.05)

                elif self.run_status == "resolved":
                    # Nothing more to do, but keep loop alive until stop()
                    await asyncio.sleep(0.05)

                else:
                    # Pending or unknown status; yield
                    await asyncio.sleep(0.05)
        except asyncio.CancelledError:
            # Graceful task cancellation on stop()
            pass


    async def _run_events_loop(self) -> None:
        while self.progress == IssueProgress.ACTIVE:
            msg = await self._q.get()  # you enqueued dicts via ingest()

            try:
                # Idempotency: skip if we've seen this id before
                eid = msg.get("id")
                if eid and eid in self._seen_event_ids:
                    continue
                if eid:
                    self._seen_event_ids.add(eid)

                etype = msg.get("type")
                payload = msg.get("payload", {})

                handler = self._handlers.get(etype)
                print(f"Executing handler for event type: {etype}", flush=True)
                if handler is None:
                    # Unknown event type; you can log or notify the client
                    print(f"Unknown event type: {etype}", flush=True)
                    continue

                await handler(payload)

            finally:
                self._q.task_done()

        # If we break out, transition to CLOSED
        self.progress = IssueProgress.CLOSED

    def start(self) -> None:
        self._issue_task = asyncio.create_task(self._run_issue_loop(), name=f"issue-{self.id}")
        self._events_task = asyncio.create_task(self._run_events_loop(), name=f"events-{self.id}")

    async def stop(self) -> None:
        if self.progress == IssueProgress.ACTIVE:
            self.progress = IssueProgress.CLOSING
        self._q.put_nowait({"type": "resolve_issue", "payload": {}, "id": str(uuid.uuid4()), "ts": datetime.datetime.utcnow().isoformat(), "source": "system"})
        for t in (getattr(self, "_issue_task", None), getattr(self, "_events_task", None)):
            if t:
                t.cancel()
                try:
                    await t
                except asyncio.CancelledError:
                    pass
        self.progress = IssueProgress.CLOSED

    
    #---- HANDLERS ----#
    def register_handlers(self) -> None:
        """
        Register handlers for the event loop.
        """
        return {
            "diagnostics.test_result": self._handle_diagnostics_test_result,
            "issue.begin": self._handle_issue_begin,
        }
    
    async def _handle_diagnostics_test_result(self, payload: Dict[str, Any]) -> None:
        await self.submit_test_result(payload.get("test_id"), payload.get("result"))

    async def _handle_issue_begin(self, payload: Dict[str, Any]) -> None:
        self.run_status = "diagnostics"
        self.tests_log.append(payload)



    async def submit_test_result(self, test_id: str, result: Any) -> None:
        """
        Update the matching test's result and wake the diagnostics loop.
        Returns the updated test dict.
        """
        async with self._state_lock:
            for test in self.tests_log:
                if test.get("id") == test_id:
                    test["result"] = result
                    # Wake the diagnostics loop to re-run agent logic
                    self._result_event.set()
                    return test

        raise ValueError(f"Test with id {test_id} not found in tests_log")









        



        

    def ingest(self, msg: Union[InboundMessage, Dict[str, Any]]) -> None:
        """
        Source-agnostic enqueue.
        Accepts InboundMessage or plain dicts (legacy); normalizes to InboundMessage.
        """
        ev = InboundMessage.ensure_envelope(msg)
        # If your queue expects dicts, push dicts; otherwise store the model.
        self._q.put_nowait(ev.model_dump())  # or put_nowait(ev) if you want models downstream



class IssueManager:
    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self.current: Optional[IssueContext] = None
        print("IssueManager initialized", flush=True)

    async def get_current(self) -> Optional[IssueContext]:
        """
        Get the current issue context.
        """
        return self.current

    async def create_issue(self) -> IssueContext:
        """
        Create a new issue context if there is not one already, or return the existing one.
        Returns the issue context and a boolean indicating if a new one was created.
        """
        async with self._lock:
            if self.current is None:
                self.current = IssueContext()
                print("Issue created", flush=True)
                return self.current
            else:
                print("Issue already exists", flush=True)
                return self.current

    async def set_connection(self, issue: IssueContext, connection: WebSocket):
        """
        Set the connection for the issue.
        """
        old = issue.connection
        if old is not None and old is not ws:
            try:
                await old.close(code=1000)
            except Exception:
                pass
        issue.connection = connection

    async def clear_connection(self, issue: IssueContext):
        """
        Clear the connection for the issue.
        """
        issue.connection = None






