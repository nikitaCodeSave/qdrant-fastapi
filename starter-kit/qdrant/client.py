"""
Клиент Qdrant.

Асинхронная обёртка над AsyncQdrantClient с:
- Управлением lifecycle (singleton)
- Health check
- Логированием
- Обработкой ошибок подключения

Принцип: Client содержит ТОЛЬКО операции с Qdrant,
никакой бизнес-логики — она в Service.

Интеграция:
    # В lifespan (main.py):
    from qdrant.client import qdrant_client

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        await qdrant_client.connect(host="localhost", port=6333)
        yield
        await qdrant_client.close()
"""

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING, Any

from qdrant_client import AsyncQdrantClient, models
from qdrant_client.http.exceptions import UnexpectedResponse

from .exceptions import (
    CollectionAlreadyExistsError,
    CollectionNotFoundError,
    PointNotFoundError,
    QdrantConnectionError,
    QdrantTimeoutError,
)

if TYPE_CHECKING:
    from qdrant_client.models import Distance, PointStruct, ScoredPoint

logger = logging.getLogger(__name__)


class QdrantClient:
    """
    Асинхронный клиент Qdrant.

    Singleton паттерн: один клиент на всё приложение.
    Управление lifecycle через lifespan в main.py.

    Attributes:
        _client: Внутренний AsyncQdrantClient.
        _initialized: Флаг инициализации.

    Example:
        >>> client = QdrantClient()
        >>> await client.connect(host="localhost", port=6333)
        >>> collections = await client.list_collections()
        >>> await client.close()
    """

    _instance: QdrantClient | None = None
    _client: AsyncQdrantClient | None = None
    _initialized: bool = False

    def __new__(cls) -> QdrantClient:
        """Singleton: возвращает существующий экземпляр или создаёт новый."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    async def connect(
        self,
        host: str | None = None,
        port: int | None = None,
        url: str | None = None,
        api_key: str | None = None,
        path: str | None = None,
        **kwargs: Any,
    ) -> None:
        """
        Инициализация подключения к Qdrant.

        Поддерживает три режима:
        1. Server Mode: host + port (или url)
        2. Cloud Mode: url + api_key
        3. Local Mode: path (embedded, без Docker)

        Args:
            host: Хост Qdrant сервера (по умолчанию localhost).
            port: Порт Qdrant сервера (по умолчанию 6333).
            url: Полный URL (альтернатива host+port).
            api_key: API ключ для аутентификации.
            path: Путь для локального хранилища (embedded режим).
            **kwargs: Дополнительные параметры AsyncQdrantClient.

        Raises:
            QdrantConnectionError: Если не удалось подключиться.

        Example:
            # Server Mode
            await client.connect(host="localhost", port=6333)

            # Cloud Mode
            await client.connect(
                url="https://xxx.cloud.qdrant.io:6333",
                api_key="your-api-key"
            )

            # Local Mode (embedded)
            await client.connect(path="./qdrant_storage")
        """
        if self._initialized:
            return

        # Определяем режим подключения
        if path:
            mode = "local"
            client_kwargs = {"path": path, **kwargs}
        elif url:
            mode = "cloud" if api_key else "server"
            client_kwargs = {"url": url, "api_key": api_key, **kwargs}
        else:
            mode = "server"
            client_kwargs = {
                "host": host or "localhost",
                "port": port or 6333,
                "api_key": api_key,
                **kwargs,
            }

        logger.info("Connecting to Qdrant: mode=%s", mode)

        try:
            self._client = AsyncQdrantClient(**client_kwargs)

            # Проверка подключения
            await self._client.get_collections()
            self._initialized = True

            logger.info("Qdrant connected successfully")

        except Exception as e:
            logger.error("Failed to connect to Qdrant: %s", e)
            raise QdrantConnectionError(
                f"Cannot connect to Qdrant: {e}",
                details={"mode": mode},
            ) from e

    async def close(self) -> None:
        """
        Закрытие подключения.

        Вызывается в lifespan при остановке приложения.
        """
        if self._client is not None:
            logger.info("Closing Qdrant connection")
            await self._client.close()
            self._client = None
            self._initialized = False

    @property
    def client(self) -> AsyncQdrantClient:
        """
        Получить внутренний клиент.

        Raises:
            QdrantConnectionError: Если клиент не инициализирован.
        """
        if self._client is None:
            raise QdrantConnectionError("Qdrant client not initialized")
        return self._client

    # =========================================================================
    # Health Check
    # =========================================================================
    async def health_check(self) -> dict[str, Any]:
        """
        Проверка состояния подключения.

        Returns:
            {
                "status": "healthy" | "unhealthy",
                "latency_ms": float,
                "collections_count": int,
                "error": str | None
            }
        """
        start = time.perf_counter()

        try:
            collections = await self.client.get_collections()
            latency = (time.perf_counter() - start) * 1000

            return {
                "status": "healthy",
                "latency_ms": round(latency, 2),
                "collections_count": len(collections.collections),
            }
        except Exception as e:
            latency = (time.perf_counter() - start) * 1000
            return {
                "status": "unhealthy",
                "latency_ms": round(latency, 2),
                "error": str(e),
            }

    # =========================================================================
    # Collections
    # =========================================================================
    async def list_collections(self) -> list[str]:
        """Получить список имён коллекций."""
        result = await self.client.get_collections()
        return [c.name for c in result.collections]

    async def collection_exists(self, name: str) -> bool:
        """Проверить существование коллекции."""
        return await self.client.collection_exists(name)

    async def get_collection_info(self, name: str) -> models.CollectionInfo:
        """
        Получить информацию о коллекции.

        Raises:
            CollectionNotFoundError: Коллекция не существует.
        """
        if not await self.collection_exists(name):
            raise CollectionNotFoundError(
                f"Collection '{name}' not found",
                details={"collection": name},
            )
        return await self.client.get_collection(name)

    async def create_collection(
        self,
        name: str,
        vector_size: int,
        distance: str = "Cosine",
        on_disk: bool = False,
    ) -> bool:
        """
        Создать коллекцию.

        Args:
            name: Имя коллекции.
            vector_size: Размерность векторов.
            distance: Метрика расстояния (Cosine, Euclid, Dot).
            on_disk: Хранить векторы на диске.

        Returns:
            True если создана успешно.

        Raises:
            CollectionAlreadyExistsError: Коллекция уже существует.
        """
        if await self.collection_exists(name):
            raise CollectionAlreadyExistsError(
                f"Collection '{name}' already exists",
                details={"collection": name},
            )

        distance_map = {
            "Cosine": models.Distance.COSINE,
            "Euclid": models.Distance.EUCLID,
            "Dot": models.Distance.DOT,
        }

        await self.client.create_collection(
            collection_name=name,
            vectors_config=models.VectorParams(
                size=vector_size,
                distance=distance_map[distance],
                on_disk=on_disk,
            ),
        )

        logger.info(
            "Created collection: %s (size=%d, distance=%s)", name, vector_size, distance
        )
        return True

    async def delete_collection(self, name: str) -> bool:
        """
        Удалить коллекцию.

        Raises:
            CollectionNotFoundError: Коллекция не существует.
        """
        if not await self.collection_exists(name):
            raise CollectionNotFoundError(
                f"Collection '{name}' not found",
                details={"collection": name},
            )

        await self.client.delete_collection(name)
        logger.info("Deleted collection: %s", name)
        return True

    # =========================================================================
    # Points (CRUD)
    # =========================================================================
    async def upsert_points(
        self,
        collection_name: str,
        points: list[models.PointStruct],
    ) -> int:
        """
        Добавить или обновить точки.

        Args:
            collection_name: Имя коллекции.
            points: Список точек для upsert.

        Returns:
            Количество обработанных точек.
        """
        await self.client.upsert(
            collection_name=collection_name,
            points=points,
            wait=True,
        )
        return len(points)

    async def get_point(
        self,
        collection_name: str,
        point_id: str | int,
        with_vector: bool = False,
    ) -> models.Record | None:
        """
        Получить точку по ID.

        Returns:
            Record или None если не найдена.
        """
        try:
            result = await self.client.retrieve(
                collection_name=collection_name,
                ids=[point_id],
                with_vectors=with_vector,
                with_payload=True,
            )
            return result[0] if result else None
        except UnexpectedResponse:
            return None

    async def delete_points(
        self,
        collection_name: str,
        point_ids: list[str | int],
    ) -> int:
        """
        Удалить точки по ID.

        Returns:
            Количество удалённых точек.
        """
        await self.client.delete(
            collection_name=collection_name,
            points_selector=models.PointIdsList(points=point_ids),
            wait=True,
        )
        return len(point_ids)

    # =========================================================================
    # Search (query_points - актуальный API)
    # =========================================================================
    async def query_points(
        self,
        collection_name: str,
        query: list[float],
        limit: int = 10,
        score_threshold: float | None = None,
        query_filter: dict | None = None,
        with_payload: bool = True,
        with_vectors: bool = False,
    ) -> list[models.ScoredPoint]:
        """
        Векторный поиск через query_points API.

        Это актуальный унифицированный метод Qdrant для поиска,
        заменяющий устаревший search().

        Args:
            collection_name: Имя коллекции.
            query: Вектор запроса.
            limit: Максимум результатов.
            score_threshold: Минимальный score (0-1 для Cosine).
            query_filter: Фильтр по payload полям.
            with_payload: Включить payload в результат.
            with_vectors: Включить вектор в результат.

        Returns:
            Список ScoredPoint отсортированный по релевантности.

        Example:
            >>> results = await client.query_points(
            ...     collection_name="documents",
            ...     query=[0.1, 0.2, ...],
            ...     limit=10,
            ...     query_filter={"category": "tech"},
            ... )
        """
        # Конвертация dict фильтра в models.Filter
        qdrant_filter = None
        if query_filter:
            qdrant_filter = self._build_filter(query_filter)

        # query_points возвращает QueryResponse, нужно взять .points
        response = await self.client.query_points(
            collection_name=collection_name,
            query=query,
            limit=limit,
            score_threshold=score_threshold,
            query_filter=qdrant_filter,
            with_payload=with_payload,
            with_vectors=with_vectors,
        )

        return response.points

    def _build_filter(self, filter_dict: dict) -> models.Filter:
        """
        Конвертирует dict в Qdrant Filter.

        Поддерживает простые условия: {"field": "value"}
        TODO: Расширить для сложных фильтров.
        """
        conditions = []

        for key, value in filter_dict.items():
            if isinstance(value, (str, int, float, bool)):
                conditions.append(
                    models.FieldCondition(
                        key=key,
                        match=models.MatchValue(value=value),
                    )
                )

        return models.Filter(must=conditions) if conditions else models.Filter()


# =============================================================================
# Глобальный экземпляр (singleton)
# =============================================================================
qdrant_client = QdrantClient()
