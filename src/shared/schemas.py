"""
Общие Pydantic схемы.

Базовые схемы, используемые во всех доменах:
- ErrorResponse: стандартный формат ошибок
- PaginationParams: параметры пагинации
- PaginatedResponse: обёртка для списков
- HealthResponse: ответ health check
"""

from datetime import datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

# TypeVar для generic пагинации
T = TypeVar("T")


class BaseSchema(BaseModel):
    """
    Базовый класс для всех схем.

    Настройки:
    - from_attributes: создание из ORM/dataclass объектов
    - populate_by_name: поддержка alias при валидации
    """

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
    )


# =============================================================================
# Error Schemas
# =============================================================================
class ErrorResponse(BaseModel):
    """
    Стандартный формат ответа с ошибкой.

    Используется в exception_handler для всех DomainError.

    Example:
        {
            "error": "not_found",
            "message": "Collection 'docs' not found",
            "details": {"collection": "docs"}
        }
    """

    error: str = Field(..., description="Машиночитаемый код ошибки")
    message: str = Field(..., description="Человекочитаемое описание")
    details: dict | None = Field(default=None, description="Дополнительные данные")


# =============================================================================
# Pagination Schemas
# =============================================================================
class PaginationParams(BaseModel):
    """
    Параметры пагинации для GET запросов.

    Example:
        >>> @router.get("/items")
        >>> async def list_items(pagination: PaginationParams = Depends()):
        >>>     ...
    """

    offset: int = Field(default=0, ge=0, description="Смещение от начала")
    limit: int = Field(default=20, ge=1, le=100, description="Количество записей")


class PaginatedResponse(BaseSchema, Generic[T]):
    """
    Обёртка для пагинированных списков.

    Example:
        >>> PaginatedResponse[DocumentResponse](
        >>>     items=[...],
        >>>     total=100,
        >>>     offset=0,
        >>>     limit=20,
        >>> )
    """

    items: list[T] = Field(..., description="Список элементов")
    total: int = Field(..., ge=0, description="Общее количество")
    offset: int = Field(..., ge=0, description="Текущее смещение")
    limit: int = Field(..., ge=1, description="Текущий лимит")

    @property
    def has_more(self) -> bool:
        """Есть ли ещё элементы после текущей страницы."""
        return self.offset + len(self.items) < self.total


# =============================================================================
# Health Schemas
# =============================================================================
class ServiceHealth(BaseModel):
    """Состояние отдельного сервиса."""

    status: str = Field(..., description="healthy | unhealthy")
    latency_ms: float | None = Field(default=None, description="Время ответа в мс")
    error: str | None = Field(default=None, description="Сообщение об ошибке")


class HealthResponse(BaseModel):
    """
    Ответ health check endpoint.

    Example:
        {
            "status": "healthy",
            "version": "0.1.0",
            "timestamp": "2025-01-01T12:00:00Z",
            "services": {
                "qdrant": {"status": "healthy", "latency_ms": 5.2}
            }
        }
    """

    status: str = Field(..., description="healthy | degraded | unhealthy")
    version: str = Field(..., description="Версия приложения")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    services: dict[str, ServiceHealth] = Field(
        default_factory=dict,
        description="Состояние зависимых сервисов",
    )
