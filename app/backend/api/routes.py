from fastapi import APIRouter

router = APIRouter()


# # Route for raising a new issue
# @router.post("/raise-issue")
# def raise_issue(issue: Issue):
#     return {"message": "Issue raised"}











# Test route
@router.get("/test")
def test():
    return {"message": "Hello, World!"}