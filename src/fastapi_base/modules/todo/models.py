from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from fastapi_base.database.base import BaseEntity


class Todo(BaseEntity):
    __tablename__ = "todos"

    title: Mapped[str] = mapped_column(String(120))
    state: Mapped[str] = mapped_column(String(20))
