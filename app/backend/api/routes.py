from fastapi import APIRouter

router = APIRouter()











# Test route
@router.get("/test")
def test():
    return {"message": "Hello, World!"}