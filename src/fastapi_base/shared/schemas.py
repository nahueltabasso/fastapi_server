from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class BaseInputDTO(BaseModel):
    """Base Input DTO."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class BaseOutputDTO(BaseModel):
    """Base Output DTO."""

    model_config = ConfigDict(from_attributes=True)
    id: int
    updated_at: datetime
    created_at: datetime
    created_user: str
    updated_user: str | None
    deleted: bool


class BaseFilterDTO(BaseModel):
    """Base Filter DTO for filtering and pagination."""

    model_config = ConfigDict(extra="forbid")
    limit: int = Field(default=10, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
    sort: str = "-created_at"


class PageDTO[T](BaseModel):
    """Generic PageDTO for paginated responses."""

    items: list[T]
    total: int
    limit: int
    offset: int
