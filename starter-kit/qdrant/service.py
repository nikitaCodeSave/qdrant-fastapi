"""
Сервис Qdrant.

ВСЯ бизнес-логика домена находится здесь:
- Валидация бизнес-правил
- Оркестрация операций
- Выброс доменных исключений

Принципы:
- Service НЕ знает о HTTP (никаких HTTPException)
- Получает Client через DI (конструктор)
- Возвращает схемы или доменные объекты
"""

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING, Any

from qdrant_client import models

from .client import QdrantClient
from .constants import PayloadFields
from .exceptions import (
    CollectionNotFoundError,
    PointNotFoundError,
    VectorSizeMismatchError,
)
from .schemas import (
    CollectionCreate,
    CollectionInfo,
    CollectionListResponse,
    PointCreate,
    PointResponse,
    SearchRequest,
    SearchResponse,
    SearchResult,
)

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class QdrantService:
    """
    Сервис для работы с Qdrant.

    Инкапсулирует бизнес-логику:
    - Управление коллекциями
    - CRUD операции с точками
    - Векторный поиск

    Attributes:
        client: QdrantClient для доступа к данным.

    Example:
        >>> service = QdrantService(client)
        >>> await service.create_collection(CollectionCreate(...))
        >>> results = await service.search("documents", SearchRequest(...))
    """

    def __init__(self, client: QdrantClient) -> None:
        """
        Инициализация сервиса.

        Args:
            client: Клиент Qdrant (инжектируется через DI).
        """
        self.client = client

    # =========================================================================
    # Collections
    # =========================================================================
    async def list_collections(self) -> CollectionListResponse:
        """
        Получить список коллекций с информацией.

        Returns:
            CollectionListResponse со списком коллекций.
        """
        names = await self.client.list_collections()
        collections = []

        for name in names:
            try:
                info = await self.get_collection(name)
                collections.append(info)
            except CollectionNotFoundError:
                # Коллекция могла быть удалена между вызовами
                continue

        return CollectionListResponse(
            collections=collections,
            total=len(collections),
        )

    async def get_collection(self, name: str) -> CollectionInfo:
        """
        Получить информацию о коллекции.

        Args:
            name: Имя коллекции.

        Returns:
            CollectionInfo с данными коллекции.

        Raises:
            CollectionNotFoundError: Коллекция не найдена.
        """
        info = await self.client.get_collection_info(name)

        # Извлекаем параметры вектора
        vector_config = info.config.params.vectors
        if isinstance(vector_config, models.VectorParams):
            vector_size = vector_config.size
            distance = vector_config.distance.value
        else:
            # Named vectors — берём первый
            first_vector = next(iter(vector_config.values()))
            vector_size = first_vector.size
            distance = first_vector.distance.value

        return CollectionInfo(
            name=name,
            vectors_count=info.vectors_count or 0,
            points_count=info.points_count or 0,
            status=info.status.value,
            vector_size=vector_size,
            distance=distance,
        )

    async def create_collection(self, data: CollectionCreate) -> CollectionInfo:
        """
        Создать новую коллекцию.

        Args:
            data: Параметры коллекции.

        Returns:
            CollectionInfo созданной коллекции.

        Raises:
            CollectionAlreadyExistsError: Коллекция уже существует.
        """
        await self.client.create_collection(
            name=data.name,
            vector_size=data.vector_size,
            distance=data.distance,
            on_disk=data.on_disk,
        )

        return await self.get_collection(data.name)

    async def delete_collection(self, name: str) -> bool:
        """
        Удалить коллекцию.

        Args:
            name: Имя коллекции.

        Returns:
            True если успешно удалена.

        Raises:
            CollectionNotFoundError: Коллекция не найдена.
        """
        return await self.client.delete_collection(name)

    # =========================================================================
    # Points
    # =========================================================================
    async def upsert_point(
        self,
        collection_name: str,
        point: PointCreate,
    ) -> PointResponse:
        """
        Добавить или обновить точку.

        Args:
            collection_name: Имя коллекции.
            point: Данные точки.

        Returns:
            PointResponse с данными точки.

        Raises:
            CollectionNotFoundError: Коллекция не найдена.
            VectorSizeMismatchError: Размерность вектора не соответствует.
        """
        # Валидация: коллекция существует
        collection_info = await self.get_collection(collection_name)

        # Валидация: размерность вектора
        if len(point.vector) != collection_info.vector_size:
            raise VectorSizeMismatchError(
                f"Expected {collection_info.vector_size}, got {len(point.vector)}",
                details={
                    "expected": collection_info.vector_size,
                    "got": len(point.vector),
                },
            )

        # Upsert
        qdrant_point = models.PointStruct(
            id=point.id,
            vector=point.vector,
            payload=point.payload,
        )
        await self.client.upsert_points(collection_name, [qdrant_point])

        return PointResponse(
            id=point.id,
            vector=point.vector,
            payload=point.payload,
        )

    async def upsert_points_batch(
        self,
        collection_name: str,
        points: list[PointCreate],
    ) -> int:
        """
        Batch upsert точек.

        Args:
            collection_name: Имя коллекции.
            points: Список точек.

        Returns:
            Количество обработанных точек.
        """
        # Валидация коллекции
        collection_info = await self.get_collection(collection_name)

        # Валидация размерности для всех точек
        for point in points:
            if len(point.vector) != collection_info.vector_size:
                raise VectorSizeMismatchError(
                    f"Point {point.id}: expected {collection_info.vector_size}, got {len(point.vector)}",
                )

        # Конвертация в PointStruct
        qdrant_points = [
            models.PointStruct(
                id=p.id,
                vector=p.vector,
                payload=p.payload,
            )
            for p in points
        ]

        return await self.client.upsert_points(collection_name, qdrant_points)

    async def get_point(
        self,
        collection_name: str,
        point_id: str | int,
        with_vector: bool = False,
    ) -> PointResponse:
        """
        Получить точку по ID.

        Raises:
            PointNotFoundError: Точка не найдена.
        """
        record = await self.client.get_point(
            collection_name,
            point_id,
            with_vector=with_vector,
        )

        if record is None:
            raise PointNotFoundError(
                f"Point '{point_id}' not found",
                details={"point_id": point_id, "collection": collection_name},
            )

        return PointResponse(
            id=record.id,
            vector=record.vector if with_vector else None,
            payload=record.payload or {},
        )

    async def delete_point(self, collection_name: str, point_id: str | int) -> bool:
        """
        Удалить точку.

        Raises:
            PointNotFoundError: Точка не найдена.
        """
        # Проверяем существование
        await self.get_point(collection_name, point_id)

        await self.client.delete_points(collection_name, [point_id])
        return True

    # =========================================================================
    # Search (query_points API)
    # =========================================================================
    async def search(
        self,
        collection_name: str,
        request: SearchRequest,
    ) -> SearchResponse:
        """
        Векторный поиск через query_points API.

        Использует актуальный унифицированный метод Qdrant query_points,
        который заменяет устаревший search().

        Args:
            collection_name: Имя коллекции.
            request: Параметры поиска (vector, limit, filters).

        Returns:
            SearchResponse с результатами и метриками.

        Raises:
            CollectionNotFoundError: Коллекция не найдена.
            VectorSizeMismatchError: Размерность вектора не соответствует.

        Example:
            >>> response = await service.search(
            ...     "documents",
            ...     SearchRequest(vector=[0.1, ...], limit=10)
            ... )
            >>> for result in response.results:
            ...     print(f"{result.id}: {result.score:.3f}")
        """
        # Валидация коллекции и размерности
        collection_info = await self.get_collection(collection_name)

        if len(request.vector) != collection_info.vector_size:
            raise VectorSizeMismatchError(
                f"Query vector: expected {collection_info.vector_size}, got {len(request.vector)}",
                details={
                    "expected": collection_info.vector_size,
                    "got": len(request.vector),
                    "collection": collection_name,
                },
            )

        # Поиск с замером времени
        start = time.perf_counter()

        # Используем актуальный query_points API
        scored_points = await self.client.query_points(
            collection_name=collection_name,
            query=request.vector,
            limit=request.limit,
            score_threshold=request.score_threshold,
            query_filter=request.query_filter,
            with_payload=request.with_payload,
            with_vectors=request.with_vector,
        )

        query_time = (time.perf_counter() - start) * 1000

        # Конвертация результатов в схемы
        results = [
            SearchResult(
                id=point.id,
                score=point.score,
                payload=point.payload if request.with_payload else None,
                vector=point.vector if request.with_vector else None,
            )
            for point in scored_points
        ]

        return SearchResponse(
            results=results,
            total=len(results),
            limit=request.limit,
            query_time_ms=round(query_time, 2),
        )

    # =========================================================================
    # Health
    # =========================================================================
    async def health_check(self) -> dict[str, Any]:
        """Проверка состояния Qdrant."""
        return await self.client.health_check()
