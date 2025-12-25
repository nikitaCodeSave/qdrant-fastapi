"""
Shared модуль.

Общие компоненты, используемые во всех доменах:
- exceptions: базовые классы исключений
- schemas: общие Pydantic схемы (пагинация, ответы)
"""

from src.shared.exceptions import (
    DomainError,
    NotFoundError,
    AlreadyExistsError,
    ValidationError,
    ConnectionError,
)
from src.shared.schemas import (
    ErrorResponse,
    PaginationParams,
    PaginatedResponse,
    HealthResponse,
)

__all__ = [
    # Exceptions
    "DomainError",
    "NotFoundError",
    "AlreadyExistsError",
    "ValidationError",
    "ConnectionError",
    # Schemas
    "ErrorResponse",
    "PaginationParams",
    "PaginatedResponse",
    "HealthResponse",
]
