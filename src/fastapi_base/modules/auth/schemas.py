from typing import Literal

from pydantic import BaseModel, EmailStr, Field, SecretStr

from fastapi_base.shared.schemas import BaseInputDTO

ClientType = Literal["web", "mobile"]


class RegisterDTO(BaseInputDTO):
    username: str = Field(max_length=255)
    email: EmailStr = Field(max_length=255)
    password: SecretStr = Field(min_length=8, max_length=255)


class LoginDTO(BaseInputDTO):
    email: EmailStr = Field(max_length=255)
    password: SecretStr = Field(max_length=255)
    client_type: ClientType = "web"


class RefreshTokenDTO(BaseInputDTO):
    refresh_token: SecretStr = Field(min_length=20, max_length=255)


class ActionTokenDTO(BaseInputDTO):
    token: SecretStr = Field(min_length=20, max_length=255)


class ResetPasswordDTO(BaseInputDTO):
    token: SecretStr = Field(min_length=20, max_length=255)
    new_password: SecretStr = Field(min_length=8, max_length=255)


class ChangePasswordDTO(BaseInputDTO):
    old_password: SecretStr = Field(min_length=8, max_length=255)
    new_password: SecretStr = Field(min_length=8, max_length=255)
    confirm_password: SecretStr = Field(min_length=8, max_length=255)


class GoogleLoginDTO(BaseInputDTO):
    id_token: SecretStr = Field(min_length=100, max_length=4096)
    client_type: ClientType = "web"


class GoogleLinkDTO(BaseInputDTO):
    id_token: SecretStr = Field(min_length=100, max_length=4096)


class TokenResponseDTO(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    refresh_token: str | None = None


class MessageDTO(BaseModel):
    message: str


class RefreshDTO(BaseInputDTO):
    refresh_token: SecretStr = Field(min_length=20, max_length=255)
