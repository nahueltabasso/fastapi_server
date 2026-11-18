from typing import Annotated

from fastapi import BackgroundTasks, Depends

from fastapi_base.api.deps import SessionDep
from fastapi_base.core.config import get_settings
from fastapi_base.core.context import RequestContext
from fastapi_base.core.deferred import DeferredTasks
from fastapi_base.core.email import EmailSender, SmtpEmailSender
from fastapi_base.modules.auth.google import GoogleVerifier, get_google_verifier
from fastapi_base.modules.auth.mailer import AuthMailer
from fastapi_base.modules.auth.repository import (
    ActionTokenRepository,
    RefreshTokenRepository,
)
from fastapi_base.modules.auth.service import AuthService
from fastapi_base.modules.auth.sessions import SessionService
from fastapi_base.modules.users.repository import (
    RoleRepository,
    UserIdentityRepository,
    UserRepository,
    UserRoleRepository,
)


def get_email_sender() -> EmailSender:
    return SmtpEmailSender(settings=get_settings())


def get_auth_service(
    session: SessionDep,
    tasks: BackgroundTasks,
    sender: Annotated[EmailSender, Depends(get_email_sender)],
    google: Annotated[GoogleVerifier, Depends(get_google_verifier)],
) -> AuthService:
    return AuthService(
        session=session,
        user_repository=UserRepository(session=session),
        role_repository=RoleRepository(session=session),
        user_role_repository=UserRoleRepository(session=session),
        user_identity_repository=UserIdentityRepository(session=session),
        action_token_repository=ActionTokenRepository(session=session),
        session_service=SessionService(RefreshTokenRepository(session=session)),
        mailer=AuthMailer(sender, get_settings()),
        google_verifier=google,
        deferred=DeferredTasks(tasks),
    )


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
ContextDep = Annotated[RequestContext, Depends(RequestContext.from_request)]
