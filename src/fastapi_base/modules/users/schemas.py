from datetime import datetime

from pydantic import BaseModel, Field

from fastapi_base.shared.schemas import BaseFilterDTO, BaseInputDTO, BaseOutputDTO


class MeDTO(BaseModel):
    id: int
    username: str | None
    email: str
    has_password: bool
    permissions: list[str]


class UserReadDTO(BaseOutputDTO):
    username: str | None
    email: str
    email_verified_at: datetime | None
    is_active: bool
    user_locked: bool
    failed_login_count: int
    last_loging_at: datetime | None


class UserUpdateDTO(BaseInputDTO):
    username: str | None = Field(None, min_length=3, max_length=50)


class UserFilterDTO(BaseFilterDTO): ...


class RoleDTO(BaseInputDTO):
    role: str = Field(..., max_length=50)


class RoleFilterDTO(BaseFilterDTO): ...


class UserRoleFilterDTO(BaseFilterDTO): ...


class AssignRoleDTO(BaseInputDTO):
    role: str = Field(max_length=50)
