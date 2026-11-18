from enum import StrEnum


class UserPermission(StrEnum):
    READ = "users:read"
    WRITE = "users:write"
    MANAGE = "users:manage"
