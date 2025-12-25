"""
Доменные исключения Qdrant.

Наследуют от базовых исключений в shared/exceptions.py.
Используются в service.py для выброса типизированных ошибок.

Принцип: Service выбрасывает эти исключения,
exception_handler в main.py конвертирует в HTTP ответы.
"""

from src.shared.exceptions import (
    AlreadyExistsError,
    ConnectionError,
    NotFoundError,
    ValidationError,
)


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
# Document/Point Exceptions
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
