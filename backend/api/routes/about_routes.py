from fastapi import APIRouter

about_router = APIRouter(prefix="/about", tags=["About"])


@about_router.get("/")
async def read_about():
    return {"message": "Welcome to the About API"}
