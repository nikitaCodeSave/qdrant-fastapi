"""
Standalone исключения для Qdrant модуля.

Объединяет базовые доменные исключения и Qdrant-специфичные.
Для интеграции в проект достаточно только этого файла.

Иерархия:
    DomainError (400) - базовый класс
    ├── NotFoundError (404)
    │   ├── CollectionNotFoundError
    │   └── PointNotFoundError
    ├── AlreadyExistsError (409)
    │   ├── CollectionAlreadyExistsError
    │   └── PointAlreadyExistsError
    ├── ValidationError (422)
    │   ├── VectorSizeMismatchError
    │   ├── InvalidVectorError
    │   └── InvalidFilterError
    └── ConnectionError (503)
        ├── QdrantConnectionError
        └── QdrantTimeoutError

Использование:
    from qdrant.exceptions import CollectionNotFoundError, DomainError

    # В exception_handler (main.py):
    @app.exception_handler(DomainError)
    async def domain_error_handler(request, exc: DomainError):
        return JSONResponse(
            status_code=exc.status_code,
            content=exc.to_dict(),
        )
"""


# =============================================================================
# Base Exceptions
# =============================================================================
class DomainError(Exception):
    """
    Базовое доменное исключение.

    Attributes:
        message: Человекочитаемое описание ошибки.
        error_code: Машиночитаемый код для клиентов.
        status_code: HTTP статус код.
        details: Дополнительные данные об ошибке.
    """

    message: str = "Domain error occurred"
    error_code: str = "domain_error"
    status_code: int = 400

    def __init__(
        self,
        message: str | None = None,
        error_code: str | None = None,
        details: dict | None = None,
    ) -> None:
        self.message = message or self.__class__.message
        self.error_code = error_code or self.__class__.error_code
        self.details = details
        super().__init__(self.message)

    def to_dict(self) -> dict:
        """Конвертация в dict для JSON ответа."""
        result = {
            "error": self.error_code,
            "message": self.message,
        }
        if self.details:
            result["details"] = self.details
        return result


class NotFoundError(DomainError):
    """Ресурс не найден (HTTP 404)."""

    message = "Resource not found"
    error_code = "not_found"
    status_code = 404


class AlreadyExistsError(DomainError):
    """Ресурс уже существует (HTTP 409 Conflict)."""

    message = "Resource already exists"
    error_code = "already_exists"
    status_code = 409


class ValidationError(DomainError):
    """Ошибка валидации бизнес-правил (HTTP 422)."""

    message = "Validation error"
    error_code = "validation_error"
    status_code = 422


class ConnectionError(DomainError):
    """Ошибка подключения к внешнему сервису (HTTP 503)."""

    message = "Service connection error"
    error_code = "connection_error"
    status_code = 503


# =============================================================================
# Collection Exceptions
# =============================================================================
class CollectionNotFoundError(NotFoundError):
    """Коллекция не найдена."""

    message = "Collection not found"
    error_code = "collection_not_found"


class CollectionAlreadyExistsError(AlreadyExistsError):
    """Коллекция уже существует."""

    message = "Collection already exists"
    error_code = "collection_already_exists"


# =============================================================================
# Point Exceptions
# =============================================================================
class PointNotFoundError(NotFoundError):
    """Точка (документ) не найдена."""

    message = "Point not found"
    error_code = "point_not_found"


class PointAlreadyExistsError(AlreadyExistsError):
    """Точка с таким ID уже существует."""

    message = "Point already exists"
    error_code = "point_already_exists"


# =============================================================================
# Validation Exceptions
# =============================================================================
class VectorSizeMismatchError(ValidationError):
    """Размерность вектора не соответствует коллекции."""

    message = "Vector size does not match collection configuration"
    error_code = "vector_size_mismatch"


class InvalidVectorError(ValidationError):
    """Некорректный вектор."""

    message = "Invalid vector data"
    error_code = "invalid_vector"


class InvalidFilterError(ValidationError):
    """Некорректный фильтр для поиска."""

    message = "Invalid filter expression"
    error_code = "invalid_filter"


# =============================================================================
# Connection Exceptions
# =============================================================================
class QdrantConnectionError(ConnectionError):
    """Ошибка подключения к Qdrant."""

    message = "Cannot connect to Qdrant"
    error_code = "qdrant_connection_error"


class QdrantTimeoutError(ConnectionError):
    """Таймаут операции Qdrant."""

    message = "Qdrant operation timed out"
    error_code = "qdrant_timeout"
