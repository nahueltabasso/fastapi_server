from pydantic import EmailStr, Field

from fastapi_base.shared.schemas import BaseFilterDTO, BaseInputDTO, BaseOutputDTO


class UserDTO(BaseInputDTO):
    username: str = Field(..., max_length=50)
    password: str = Field(..., min_length=8, max_length=25)
    email: EmailStr = Field(..., max_length=255)
    google_user: bool = False
    first_login: bool = True
    user_locked: bool = False
    fails_attemps: int = 0
    email_verified: bool = False


class UserReadDTO(BaseOutputDTO):
    username: str
    email: EmailStr
    google_user: bool
    first_login: bool
    user_locked: bool
    fails_attemps: int
    email_verified: bool


class UserFilterDTO(BaseFilterDTO): ...


class RoleDTO(BaseInputDTO):
    name: str = Field(..., max_length=50)


class RoleFilterDTO(BaseFilterDTO): ...


class RoleReadDTO(BaseOutputDTO):
    name: str


class UserRoleFilterDTO(BaseFilterDTO): ...
