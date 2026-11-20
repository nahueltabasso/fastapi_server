from sqlalchemy import BigInteger, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from fastapi_base.database.base import BaseEntity


class Todo(BaseEntity):
    __tablename__ = "todos"

    title: Mapped[str] = mapped_column(String(120))
    state: Mapped[str] = mapped_column(String(20))
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("auth_users.id", ondelete="CASCADE"), index=True
    )
