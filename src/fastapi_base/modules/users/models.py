from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, String, text
from sqlalchemy.orm import Mapped, mapped_column

from fastapi_base.database.base import BaseEntity


class User(BaseEntity):
    __tablename__ = "auth_users"
    __table_args__ = (
        Index(
            "uq_auth_users_email_active",
            "email",
            unique=True,
            postgresql_where=text("NOT deleted"),
        ),
        Index(
            "uq_auth_users_username_active",
            "username",
            unique=True,
            postgresql_where=text("NOT deleted"),
        ),
    )

    username: Mapped[str] = mapped_column(String(50), unique=True)
    password: Mapped[str | None] = mapped_column(String(255))
    email: Mapped[str] = mapped_column(String(255), unique=True)
    is_active: Mapped[bool] = mapped_column(default=True)
    user_locked: Mapped[bool] = mapped_column(default=False)
    failed_login_count: Mapped[int] = mapped_column(default=0)
    last_loging_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    email_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Role(BaseEntity):
    __tablename__ = "auth_roles"
    __table_args__ = (
        Index(
            "uq_auth_roles_role_active",
            "role",
            unique=True,
            postgresql_where=text("NOT deleted"),
        ),
    )
    role: Mapped[str] = mapped_column(String(50), unique=True)


class UserRole(BaseEntity):
    __tablename__ = "auth_user_roles"
    __table_args__ = Index(
        "uq_user_roles_user_role_active",
        "user_id",
        "role_id",
        unique=True,
        postgresql_where="NOT deleted",
    )

    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("auth_users.id", ondelete="CASCADE")
    )
    role_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("auth_roles.id", ondelete="RESTRICT"), index=True
    )


class RolePermission(BaseEntity):
    __tablename__ = "auth_role_permissions"
    __table_args__ = Index(
        "uq_auth_role_permissions_active",
        "role_id",
        "permission",
        unique=True,
        postgresql_where=text("NOT deleted"),
    )
    role_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("auth_roles.id", ondelete="CASCADE"), index=True
    )
    permission: Mapped[str] = mapped_column(String(50))


class UserIdentity(BaseEntity):
    __tablename__ = "auth_user_identities"
    __table_args__ = Index(
        "uq_auth_user_identities_active",
        "provider",
        "subject",
        unique=True,
        postgresql_where=text("NOT deleted"),
    )

    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("auth_users.id", ondelete="CASCADE"), index=True
    )
    provider: Mapped[str] = mapped_column(String(50))
    subject: Mapped[str] = mapped_column(String(255))
    email: Mapped[str] = mapped_column(String(255))
