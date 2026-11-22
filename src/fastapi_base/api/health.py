from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class HealthDTO(BaseModel):
    status: str


@router.get("/health")
async def health() -> HealthDTO:
    return HealthDTO(status="ok")
