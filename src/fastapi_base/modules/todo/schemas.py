from pydantic import Field

from fastapi_base.shared.schemas import BaseFilterDTO, BaseInputDTO, BaseOutputDTO


class TodoCreateDTO(BaseInputDTO):
    title: str = Field(..., max_length=120)
    state: str = Field(max_length=20, default="PENDING")


class TodoReadDTO(BaseOutputDTO):
    title: str
    state: str


class TodoFilterDTO(BaseFilterDTO):
    state: str | None = Field(None, max_length=20)
