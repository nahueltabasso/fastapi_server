from typing import Any

from sqlalchemy import event
from sqlalchemy.orm import Session

from fastapi_base.core.context import current_user
from fastapi_base.database.base import BaseEntity


@event.listens_for(Session, "before_flush")
def fill_audit_columns(session: Session, flush_context: Any, instances: Any) -> None:
    """Complete created_user and updated_user with the request's user"""
    user = current_user.get()
    if user is None:
        return
    for obj in session.new:
        if isinstance(obj, BaseEntity):
            obj.created_user = user
    for obj in session.dirty:
        if isinstance(obj, BaseEntity) and session.is_modified(obj):
            obj.updated_user = user
