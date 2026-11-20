from datetime import UTC, datetime, timedelta

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_base.core.config import get_settings
from fastapi_base.core.context import RequestContext
from fastapi_base.core.deferred import DeferredTasks
from fastapi_base.core.exceptions import BusinessLogicError, ErrorCode
from fastapi_base.core.security.passwords import (
    check_password_policy,
    hash_password,
    verify_password,
)
from fastapi_base.core.security.principal import Principal
from fastapi_base.modules.auth.google import GoogleVerifier
from fastapi_base.modules.auth.mailer import AuthMailer
from fastapi_base.modules.auth.models import TokenPurpose
from fastapi_base.modules.auth.repository import ActionTokenRepository
from fastapi_base.modules.auth.schemas import (
    ActionTokenDTO,
    ChangePasswordDTO,
    LoginDTO,
    RegisterDTO,
    ResetPasswordDTO,
)
from fastapi_base.modules.auth.sessions import SessionService, TokenPair
from fastapi_base.modules.users.models import User, UserRole
from fastapi_base.modules.users.repository import (
    RoleRepository,
    UserIdentityRepository,
    UserRepository,
    UserRoleRepository,
)
from fastapi_base.shared.transaction import TransactionalService

DEFAULT_ROLE = "user"
GOOGLE = "google"

logger = structlog.get_logger(__name__)


class AuthService(TransactionalService):
    """Authentication services for auth user cases, such as login, registration, and token management."""

    def __init__(
        self,
        session: AsyncSession,
        *,
        user_repository: UserRepository,
        role_repository: RoleRepository,
        user_role_repository: UserRoleRepository,
        user_identity_repository: UserIdentityRepository,
        action_token_repository: ActionTokenRepository,
        session_service: SessionService,
        mailer: AuthMailer,
        google_verifier: GoogleVerifier,
        deferred: DeferredTasks,
    ) -> None:
        super().__init__(session)
        self.user_repository = user_repository
        self.role_repository = role_repository
        self.user_role_repository = user_role_repository
        self.user_identity_repository = user_identity_repository
        self.action_token_repository = action_token_repository
        self.session_service = session_service
        self.mailer = mailer
        self.google_verifier = google_verifier
        self.deferred = deferred
        settings = get_settings()
        self.verify_ttl = timedelta(hours=settings.email_verification_ttl_hours)
        self.reset_ttl = timedelta(minutes=settings.password_reset_ttl_minutes)

    async def register_user(self, dataDTO: RegisterDTO) -> None:
        """Register a new user with the provided data and context."""
        password = dataDTO.password.get_secret_value()
        check_password_policy(password=password, email=dataDTO.email)

        if (
            dataDTO.password.get_secret_value()
            != dataDTO.confirm_password.get_secret_value()
        ):
            raise BusinessLogicError(
                message="Passwords do not match",
                error_code=ErrorCode.PASSWORD_NOT_MATCH,
            )

        password_hash = await hash_password(password=password)
        raw_token: str | None = None

        async with self.transaction():
            if await self.user_repository.find_by_email(email=dataDTO.email) is None:
                user: User = await self.user_repository.save(
                    User(
                        username=dataDTO.username,
                        email=dataDTO.email,
                        password=password_hash,
                    )
                )
                await self._assign_default_role(user_id=user.id)
                raw_token = await self.action_token_repository.issue(
                    user_id=user.id,
                    purpose=TokenPurpose.VERIFY_EMAIL,
                    ttl=self.verify_ttl,
                )

        if raw_token is not None:
            self.deferred.add(
                self.mailer.send_verification_email, user.email, raw_token
            )

    async def verify_email(self, dataDTO: ActionTokenDTO) -> None:
        """Verify the user's email using the provided action token."""
        verified = False
        async with self.transaction():
            token = await self.action_token_repository.consume(
                raw=dataDTO.token.get_secret_value(),
                purpose=TokenPurpose.VERIFY_EMAIL,
            )
            logger.info("Consumed token", token=token)
            user: User | None = await self.user_repository.get_by_id(
                entity_id=token.user_id  # type: ignore
            )
            if user is not None:
                user.email_verified_at = datetime.now(UTC)
                user.is_active = True
                verified = True

        if not verified:
            raise BusinessLogicError(
                message="Invalid or expired verification token",
                error_code=ErrorCode.INVALID_TOKEN,
            )

    async def resend_verification_email(self, email: str) -> None:
        """Resend the verification email to the user given its email address."""
        raw_token: str | None = None
        async with self.transaction():
            user: User | None = await self.user_repository.find_by_email(email=email)
            if user is None:
                raise BusinessLogicError(
                    message="User not found", error_code=ErrorCode.NOT_FOUND
                )
            if user is not None and user.email_verified_at is None:
                raw_token = await self.action_token_repository.issue(
                    user_id=user.id,
                    purpose=TokenPurpose.VERIFY_EMAIL,
                    ttl=self.verify_ttl,
                )
        if raw_token is not None:
            self.deferred.add(self.mailer.send_verification_email, email, raw_token)

    async def login(
        self, dataDTO: LoginDTO, request_context: RequestContext
    ) -> TokenPair:
        """Authenticate the user and return a token pair."""
        user: User | None = await self.user_repository.find_by_email(
            email=dataDTO.email
        )
        if user is None:
            raise BusinessLogicError(
                message="Invalid credentials", error_code=ErrorCode.INVALID_CREDENTIALS
            )
        if user.user_locked is True:
            raise BusinessLogicError(
                message="User account is locked", error_code=ErrorCode.USER_LOCKED
            )
        if user.email_verified_at is None:
            raise BusinessLogicError(
                message="Email not verified", error_code=ErrorCode.EMAIL_NOT_VERIFIED
            )
        valid, new_hash = await verify_password(
            dataDTO.password.get_secret_value(), user.password
        )
        pair: TokenPair | None = None
        async with self.transaction():
            if not valid or not user.is_active:
                user.register_failed_login()
            elif user.email_verified_at is not None:
                user.register_successful_login()
                if new_hash is not None:
                    user.password = new_hash  # change Argon2 parameters
                pair = await self.session_service.start(
                    user_id=user.id,
                    client_type=dataDTO.client_type,
                    request_context=request_context,
                )
        if pair is not None:
            return pair
        raise BusinessLogicError(
            message="Invalid credentials", error_code=ErrorCode.INVALID_CREDENTIALS
        )

    async def refresh_token(
        self, raw_token: str, request_context: RequestContext
    ) -> TokenPair:
        """Refresh the token pair using the provided raw token."""
        async with self.transaction():
            pair, _ = await self.session_service.rotate(
                raw_token=raw_token, request_context=request_context
            )
            if pair is None:
                raise BusinessLogicError(
                    message="Invalid session", error_code=ErrorCode.UNAUTHORIZED
                )
            return pair

    async def logout(self, raw_token: str) -> None:
        """Logout the user represented by the given principal."""
        async with self.transaction():
            await self.session_service.end(raw_token=raw_token)

    async def logout_all(self, principal: Principal) -> None:
        """Logout all sessions for the user represented by the given principal."""
        async with self.transaction():
            await self.session_service.end_all(user_id=principal.user_id)

    async def forgot_password(self, email: str) -> None:
        """Initiate the forgot password process for the user with the given email."""
        raw_token: str | None = None
        user = await self.user_repository.find_by_email(email=email)
        if user is None:
            raise BusinessLogicError(
                message="User not found", error_code=ErrorCode.NOT_FOUND
            )
        if not user.is_active or user.email_verified_at is None:
            raise BusinessLogicError(
                message="User is not active or email not verified",
                error_code=ErrorCode.UNAUTHORIZED,
            )
        async with self.transaction():
            raw_token = await self.action_token_repository.issue(
                user_id=user.id, purpose=TokenPurpose.RESET_PASSWORD, ttl=self.reset_ttl
            )
        if raw_token is not None:
            self.deferred.add(self.mailer.send_password_reset_email, email, raw_token)

    async def reset_password(self, dataDTO: ResetPasswordDTO) -> None:
        """Reset the password for the user using the provided token and new password."""
        new_password = dataDTO.new_password.get_secret_value()
        confirm_password = dataDTO.confirm_password.get_secret_value()
        if new_password != confirm_password:
            raise BusinessLogicError(
                message="Passwords do not match",
                error_code=ErrorCode.PASSWORD_NOT_MATCH,
            )
        notify: str | None = None
        async with self.transaction():
            action_token = await self.action_token_repository.consume(
                raw=dataDTO.token.get_secret_value(),
                purpose=TokenPurpose.RESET_PASSWORD,
            )
            if action_token is not None:
                user = await self.user_repository.get_by_id(
                    entity_id=action_token.user_id
                )
                if user is not None:
                    check_password_policy(password=new_password, email=user.email)
                    user.password = await hash_password(new_password)
                    user.failed_login_count, user.user_locked = 0, False
                    await self.session_service.end_all(user_id=user.id)
                    notify = user.email
            if notify is None:
                raise BusinessLogicError(
                    message="Failed to reset password",
                    error_code=ErrorCode.INVALID_TOKEN,
                )
            self.deferred.add(self.mailer.send_password_changed_email, notify)

    async def change_password(
        self, dataDTO: ChangePasswordDTO, principal: Principal
    ) -> None:
        """Change the password for the currently authenticated user."""
        user: User | None = await self.user_repository.get_by_id(
            entity_id=principal.user_id
        )
        if user is None:
            raise BusinessLogicError(
                message="Invalid session", error_code=ErrorCode.UNAUTHORIZED
            )

        # Check if the old password is correct
        valid, _ = await verify_password(
            password=dataDTO.old_password.get_secret_value(),
            password_hash=user.password,
        )
        if not valid:
            raise BusinessLogicError(
                message="Invalid current password", error_code=ErrorCode.UNAUTHORIZED
            )

        # Save the new password for the user
        new_password = dataDTO.new_password.get_secret_value()
        check_password_policy(password=new_password, email=user.email)
        new_password_hash = await hash_password(new_password)

        async with self.transaction():
            user.password = new_password_hash
            await self.session_service.end_all(user_id=user.id)

        self.deferred.add(self.mailer.send_password_changed_email, user.email)

    async def _assign_default_role(self, user_id: int) -> None:
        """Assign the default role to the user with the given ID."""
        role = await self.role_repository.find_by_role(role=DEFAULT_ROLE)
        if role is None:
            raise BusinessLogicError(
                message="Role not found", error_code=ErrorCode.NOT_FOUND
            )
        await self.user_role_repository.save(
            UserRole(
                user_id=user_id,
                role_id=role.id,
            )
        )
