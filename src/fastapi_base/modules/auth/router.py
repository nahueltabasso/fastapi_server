from typing import Annotated

import structlog
from fastapi import APIRouter, Body, Request, Response, status

from fastapi_base.api.deps import CurrentPrincipal
from fastapi_base.modules.auth.cookies import (
    clear_refresh_cookie,
    deliver_tokens,
    read_refresh_token,
)
from fastapi_base.modules.auth.dependencies import AuthServiceDep, ContextDep
from fastapi_base.modules.auth.schemas import (
    ActionTokenDTO,
    ChangePasswordDTO,
    LoginDTO,
    MessageDTO,
    RefreshDTO,
    RegisterDTO,
    ResetPasswordDTO,
    TokenResponseDTO,
)

logger = structlog.get_logger(__name__)


router = APIRouter(prefix="/auth", tags=["auth"])

OptionalRefresh = Annotated[RefreshDTO | None, Body()]


# Authentication endpoints
@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    dataDTO: RegisterDTO, service: AuthServiceDep, request_context: ContextDep
) -> MessageDTO:
    logger.info("Register endpoint called", data=dataDTO)
    await service.register_user(dataDTO=dataDTO)
    return MessageDTO(message="User registered successfully")


@router.post("/verify-email", status_code=status.HTTP_204_NO_CONTENT)
async def verify_email(dataDTO: ActionTokenDTO, service: AuthServiceDep) -> None:
    logger.info("Verify email endpoint called", data=dataDTO)
    await service.verify_email(dataDTO=dataDTO)


@router.post("/verify-email/resend", status_code=status.HTTP_202_ACCEPTED)
async def resend_verification_email(email: str, service: AuthServiceDep) -> MessageDTO:
    logger.info("Resend verification email endpoint called", email=email)
    await service.resend_verification_email(email=email)
    return MessageDTO(message="Verification email resent successfully")


@router.post("/login", status_code=status.HTTP_200_OK)
async def login(
    dataDTO: LoginDTO,
    response: Response,
    service: AuthServiceDep,
    request_context: ContextDep,
) -> TokenResponseDTO:
    logger.info("Login endpoint called", data=dataDTO)
    return deliver_tokens(
        pair=await service.login(dataDTO, request_context), response=response
    )


@router.post("/refresh", status_code=status.HTTP_200_OK)
async def refresh(
    request: Request,
    response: Response,
    service: AuthServiceDep,
    request_context: ContextDep,
    body: OptionalRefresh = None,
) -> TokenResponseDTO:
    logger.info("Refresh endpoint called")
    pair = await service.refresh_token(
        read_refresh_token(request, body), request_context
    )
    return deliver_tokens(pair=pair, response=response)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    request: Request,
    response: Response,
    service: AuthServiceDep,
    body: OptionalRefresh = None,
) -> None:
    logger.info("Logout endpoint called")
    await service.logout(read_refresh_token(request, body))
    clear_refresh_cookie(response)


@router.post("/logout-all", status_code=status.HTTP_204_NO_CONTENT)
async def logout_all(
    response: Response,
    principal: CurrentPrincipal,
    service: AuthServiceDep,
) -> None:
    logger.info("Logout all endpoint called")
    await service.logout_all(principal)
    clear_refresh_cookie(response)


# Password management endpoints
@router.post("/password/forgot-password", status_code=status.HTTP_202_ACCEPTED)
async def forgot_password(email: str, service: AuthServiceDep) -> MessageDTO:
    logger.info("Forgot password endpoint called", email=email)
    await service.forgot_password(email=email)
    return MessageDTO(message="Password reset email sent successfully")


@router.post("/password/reset-password", status_code=status.HTTP_204_NO_CONTENT)
async def reset_password(
    dataDTO: ResetPasswordDTO, response: Response, service: AuthServiceDep
) -> None:
    logger.info("Reset password endpoint called", data=dataDTO)
    await service.reset_password(dataDTO)
    clear_refresh_cookie(response)


@router.post("/password/change-password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    dataDTO: ChangePasswordDTO, principal: CurrentPrincipal, service: AuthServiceDep
) -> None:
    logger.info("Change password endpoint called", data=dataDTO)
    await service.change_password(dataDTO, principal)
