from enum import StrEnum


class TodoPermission(StrEnum):
    READ = "todos:read"
    WRITE = "todos:write"
