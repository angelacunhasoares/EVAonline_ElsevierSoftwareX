from fastapi import APIRouter

eto_router = APIRouter(prefix="/eto_calculator", tags=["ETo Calculator"])


@eto_router.get("/")
async def read_eto_calculator():
    return {"message": "Welcome to the ETo Calculator API"}
