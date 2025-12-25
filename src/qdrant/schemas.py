"""
Pydantic схемы домена Qdrant.

Паттерн схем:
- *Create: POST body (обязательные поля)
- *Update: PATCH body (все опционально)
- *Response: GET response (включает id, timestamps)
- *Params: Query parameters

Правило: НЕ возвращать сырые объекты Qdrant из API,
всегда конвертировать в Pydantic схемы.
"""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from src.qdrant.constants import (
    DEFAULT_SEARCH_LIMIT,
    MAX_COLLECTION_NAME_LENGTH,
    MAX_SEARCH_LIMIT,
    MAX_TEXT_FIELD_LENGTH,
    MAX_VECTOR_SIZE,
    MIN_COLLECTION_NAME_LENGTH,
    MIN_VECTOR_SIZE,
    Distance,
)


# =============================================================================
# Base Schema
# =============================================================================
class QdrantBaseSchema(BaseModel):
    """Базовая схема с общими настройками."""

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
    )


# =============================================================================
# Collection Schemas
# =============================================================================
class CollectionCreate(BaseModel):
    """
    Создание коллекции.

    Example:
        {
            "name": "documents",
            "vector_size": 1024,
            "distance": "Cosine"
        }
    """

    name: str = Field(
        ...,
        min_length=MIN_COLLECTION_NAME_LENGTH,
        max_length=MAX_COLLECTION_NAME_LENGTH,
        description="Имя коллекции",
        examples=["documents", "products"],
    )
    vector_size: int = Field(
        ...,
        ge=MIN_VECTOR_SIZE,
        le=MAX_VECTOR_SIZE,
        description="Размерность векторов",
        examples=[1024, 1536],
    )
    distance: Literal["Cosine", "Euclid", "Dot"] = Field(
        default=Distance.COSINE,
        description="Метрика расстояния",
    )
    on_disk: bool = Field(
        default=False,
        description="Хранить векторы на диске (экономия RAM)",
    )


class CollectionInfo(QdrantBaseSchema):
    """
    Информация о коллекции.

    Example:
        {
            "name": "documents",
            "vectors_count": 1500,
            "points_count": 1500,
            "status": "green",
            "vector_size": 1024,
            "distance": "Cosine"
        }
    """

    name: str
    vectors_count: int = Field(..., ge=0)
    points_count: int = Field(..., ge=0)
    status: str = Field(..., description="green | yellow | red")
    vector_size: int
    distance: str


class CollectionListResponse(BaseModel):
    """Список коллекций."""

    collections: list[CollectionInfo]
    total: int = Field(..., ge=0)


# =============================================================================
# Point/Document Schemas
# =============================================================================
class PointCreate(BaseModel):
    """
    Создание точки (документа с вектором).

    Example:
        {
            "id": "doc_123",
            "vector": [0.1, 0.2, ...],
            "payload": {"text": "...", "metadata": {...}}
        }
    """

    id: str | int = Field(..., description="Уникальный ID точки")
    vector: list[float] = Field(..., min_length=1, description="Вектор embedding")
    payload: dict[str, Any] = Field(
        default_factory=dict,
        description="Метаданные документа",
    )


class PointsBatchCreate(BaseModel):
    """Batch создание точек."""

    points: list[PointCreate] = Field(..., min_length=1, max_length=1000)


class PointResponse(QdrantBaseSchema):
    """Ответ с данными точки."""

    id: str | int
    vector: list[float] | None = Field(default=None, description="Вектор (если запрошен)")
    payload: dict[str, Any]
    score: float | None = Field(default=None, description="Score при поиске")


# =============================================================================
# Search Schemas
# =============================================================================
class SearchRequest(BaseModel):
    """
    Запрос векторного поиска.

    Example:
        {
            "vector": [0.1, 0.2, ...],
            "limit": 10,
            "score_threshold": 0.7,
            "with_payload": true
        }
    """

    vector: list[float] = Field(..., min_length=1, description="Вектор запроса")
    limit: int = Field(
        default=DEFAULT_SEARCH_LIMIT,
        ge=1,
        le=MAX_SEARCH_LIMIT,
        description="Количество результатов",
    )
    score_threshold: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Минимальный score (только для Cosine)",
    )
    with_payload: bool = Field(default=True, description="Включить payload в ответ")
    with_vector: bool = Field(default=False, description="Включить вектор в ответ")
    filter: dict[str, Any] | None = Field(
        default=None,
        description="Фильтр по payload полям",
    )


class SearchByTextRequest(BaseModel):
    """
    Поиск по тексту (требует embedding service).

    Example:
        {
            "text": "How to configure Qdrant?",
            "limit": 10
        }
    """

    text: str = Field(
        ...,
        min_length=1,
        max_length=MAX_TEXT_FIELD_LENGTH,
        description="Текст запроса",
    )
    limit: int = Field(default=DEFAULT_SEARCH_LIMIT, ge=1, le=MAX_SEARCH_LIMIT)
    score_threshold: float | None = Field(default=None, ge=0.0, le=1.0)
    filter: dict[str, Any] | None = None


class SearchResult(QdrantBaseSchema):
    """Результат поиска."""

    id: str | int
    score: float = Field(..., description="Релевантность (0-1 для Cosine)")
    payload: dict[str, Any] | None = None
    vector: list[float] | None = None


class SearchResponse(BaseModel):
    """Ответ поиска."""

    results: list[SearchResult]
    total: int = Field(..., ge=0, description="Количество найденных")
    limit: int
    query_time_ms: float | None = Field(default=None, description="Время выполнения")


# =============================================================================
# Document Schemas (высокоуровневые)
# =============================================================================
class DocumentCreate(BaseModel):
    """
    Создание документа (без вектора — будет вычислен).

    Используется когда embedding вычисляется на стороне сервиса.

    Example:
        {
            "id": "doc_123",
            "text": "Содержание документа...",
            "metadata": {"source": "manual.pdf"}
        }
    """

    id: str = Field(..., min_length=1, description="Уникальный ID документа")
    text: str = Field(
        ...,
        min_length=1,
        max_length=MAX_TEXT_FIELD_LENGTH,
        description="Текст документа",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Дополнительные метаданные",
    )


class DocumentResponse(QdrantBaseSchema):
    """Ответ с данными документа."""

    id: str
    text: str
    metadata: dict[str, Any]
    score: float | None = None
    created_at: datetime | None = None
