from enum import StrEnum

from pydantic import Field

from fastapi_base.shared.schemas import BaseFilterDTO, BaseInputDTO, BaseOutputDTO


class TodoState(StrEnum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"


class TodoCreateDTO(BaseInputDTO):
    title: str = Field(..., max_length=120)
    state: TodoState = Field(default=TodoState.PENDING)
    user_id: int


class TodoUpdateDTO(BaseInputDTO):
    title: str | None = Field(None, max_length=120)
    state: TodoState | None = Field(None)


class TodoReadDTO(BaseOutputDTO):
    title: str
    state: TodoState
    user_id: int


class TodoFilterDTO(BaseFilterDTO):
    state: TodoState | None = Field(None)
