from sqlalchemy import BigInteger, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from fastapi_base.database.base import BaseEntity


class User(BaseEntity):
    __tablename__ = "auth_users"

    username: Mapped[str] = mapped_column(String(50), unique=True)
    password: Mapped[str] = mapped_column(String(255))
    email: Mapped[str] = mapped_column(String(255), unique=True)
    google_user: Mapped[bool] = mapped_column(default=False)
    first_login: Mapped[bool] = mapped_column(default=True)
    user_locked: Mapped[bool] = mapped_column(default=False)
    fails_attemps: Mapped[int] = mapped_column(default=0)
    email_verified: Mapped[bool] = mapped_column(default=False)


class Role(BaseEntity):
    __tablename__ = "auth_roles"

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
