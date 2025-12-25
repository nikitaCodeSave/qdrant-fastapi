"""
Qdrant модуль для FastAPI.

Готовый к интеграции модуль для работы с векторной БД Qdrant.

Возможности:
- CRUD операции с коллекциями
- Добавление и получение точек (векторов с payload)
- Batch операции (до 1000 точек)
- Векторный поиск с фильтрами
- Health check

Быстрый старт:
    from qdrant import router as qdrant_router
    from qdrant.client import qdrant_client

    # В lifespan
    await qdrant_client.connect(host="localhost", port=6333)

    # Подключение роутера
    app.include_router(qdrant_router, prefix="/api/v1")

Документация: см. README.md
"""

from .router import router
from .client import qdrant_client, QdrantClient
from .service import QdrantService
from .exceptions import (
    DomainError,
    CollectionNotFoundError,
    CollectionAlreadyExistsError,
    PointNotFoundError,
    VectorSizeMismatchError,
    QdrantConnectionError,
)

__all__ = [
    # Router
    "router",
    # Client
    "qdrant_client",
    "QdrantClient",
    # Service
    "QdrantService",
    # Exceptions
    "DomainError",
    "CollectionNotFoundError",
    "CollectionAlreadyExistsError",
    "PointNotFoundError",
    "VectorSizeMismatchError",
    "QdrantConnectionError",
]
