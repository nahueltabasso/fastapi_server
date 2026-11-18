import uuid
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Principal:
    """Who made the request and its privileges. Inmutable and without ORM"""

    user_id: int
    session_id: uuid.UUID
    permissions: frozenset[str]

    def has(self, permission: str) -> bool:
        return permission in self.permissions
