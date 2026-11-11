from datetime import datetime

from pydantic import Field

from fastapi_base.shared.schemas import BaseFilterDTO, BaseInputDTO, BaseOutputDTO

# class UserDTO(BaseInputDTO):
#     username: str = Field(..., max_length=50)
#     password: str = Field(..., min_length=8, max_length=25)
#     email: EmailStr = Field(..., max_length=255)
#     google_user: bool = False
#     first_login: bool = True
#     user_locked: bool = False
#     fails_attemps: int = 0


class UserReadDTO(BaseOutputDTO):
    username: str | None
    email: str
    email_verified_at: datetime | None
    is_active: bool
    user_locked: bool
    failed_login_count: int
    last_loging_at: datetime | None


class UserUpdateDTO(BaseInputDTO):
    username: str | None = Field(
        None, min_length=3, max_length=50, pattern="^[a-zA-Z0-9_]+$"
    )


class UserFilterDTO(BaseFilterDTO): ...


class RoleDTO(BaseInputDTO):
    role: str = Field(..., max_length=50)


class RoleFilterDTO(BaseFilterDTO): ...


class UserRoleFilterDTO(BaseFilterDTO): ...


class AssignRoleDTO(BaseInputDTO):
    role: str = Field(max_length=50)
