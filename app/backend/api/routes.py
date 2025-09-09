from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Request

router = APIRouter()


# # Route for raising a new issue
# @router.post("/raise-issue")
# def raise_issue(issue: Issue):
#     return {"message": "Issue raised"}


"""
ROUTE: "/issue/create"
This route can be called to create a new issue, which starts the diagnostics process. 
Calling the route will:
- Create a new globally accessible issue (object holding an issue context).
- Handle the creation of a websocket connection to the client.
- Inform the user if an issue is already in progress and return the issue id.
"""
@router.websocket("/issue/create")
async def create_issue(websocket: WebSocket):
    await websocket.accept()
    app_data = websocket.app.state

    # check if an issue is already in progress, if so close the connection
    issue = await app_data.issue_manager.get_current()
    if issue is not None:
        await websocket.send_json({"type": "issue.create_rejected", "reason": "active_issue_exists"})
        await websocket.close(code=1008, reason="active_issue_exists")
        return
    
    # create a new issue
    issue = await app_data.issue_manager.create_issue()

    # set the connection for the issue
    await app_data.issue_manager.set_connection(issue, websocket)
    print(f"Issue created: {issue.id}", flush=True)



"""
ROUTE: "/issue/current"
"""

"""
ROUTE: "/issue/"
"""











# Test route
@router.get("/test")
def test():
    return {"message": "Hello, World!"}