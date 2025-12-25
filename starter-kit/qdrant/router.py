"""
HTTP роутер домена Qdrant.

ПРАВИЛО: Роутер должен быть ТОНКИМ!
- Только HTTP: принимает request, возвращает response
- Делегирует ВСЮ логику в Service
- НЕ содержит бизнес-логики
- НЕ обращается к Client напрямую

Паттерн:
    @router.post("/")
    async def create(
        data: CreateSchema,
        service: Service = Depends(get_service),
    ) -> ResponseSchema:
        result = await service.create(data)
        return ResponseSchema.model_validate(result)
"""

from fastapi import APIRouter, Depends, status

from .dependencies import QdrantServiceDep
from .schemas import (
    CollectionCreate,
    CollectionInfo,
    CollectionListResponse,
    PointCreate,
    PointResponse,
    PointsBatchCreate,
    SearchRequest,
    SearchResponse,
)

router = APIRouter(prefix="/qdrant", tags=["qdrant"])


# =============================================================================
# Collections
# =============================================================================
@router.get(
    "/collections",
    response_model=CollectionListResponse,
    summary="Список коллекций",
)
async def list_collections(service: QdrantServiceDep) -> CollectionListResponse:
    """
    Получить список всех коллекций с информацией.

    Returns:
        Список коллекций с количеством точек и настройками.
    """
    return await service.list_collections()


@router.get(
    "/collections/{name}",
    response_model=CollectionInfo,
    summary="Информация о коллекции",
)
async def get_collection(name: str, service: QdrantServiceDep) -> CollectionInfo:
    """
    Получить информацию о коллекции.

    Args:
        name: Имя коллекции.

    Returns:
        Информация о коллекции.

    Raises:
        404: Коллекция не найдена.
    """
    return await service.get_collection(name)


@router.post(
    "/collections",
    response_model=CollectionInfo,
    status_code=status.HTTP_201_CREATED,
    summary="Создать коллекцию",
)
async def create_collection(
    data: CollectionCreate,
    service: QdrantServiceDep,
) -> CollectionInfo:
    """
    Создать новую коллекцию.

    Args:
        data: Параметры коллекции (имя, размерность, метрика).

    Returns:
        Информация о созданной коллекции.

    Raises:
        409: Коллекция уже существует.
    """
    return await service.create_collection(data)


@router.delete(
    "/collections/{name}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить коллекцию",
)
async def delete_collection(name: str, service: QdrantServiceDep) -> None:
    """
    Удалить коллекцию и все её данные.

    Args:
        name: Имя коллекции.

    Raises:
        404: Коллекция не найдена.
    """
    await service.delete_collection(name)


# =============================================================================
# Points
# =============================================================================
@router.post(
    "/collections/{collection_name}/points",
    response_model=PointResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Добавить точку",
)
async def upsert_point(
    collection_name: str,
    point: PointCreate,
    service: QdrantServiceDep,
) -> PointResponse:
    """
    Добавить или обновить точку (документ с вектором).

    Args:
        collection_name: Имя коллекции.
        point: Данные точки (id, vector, payload).

    Returns:
        Данные добавленной точки.

    Raises:
        404: Коллекция не найдена.
        422: Размерность вектора не соответствует коллекции.
    """
    return await service.upsert_point(collection_name, point)


@router.post(
    "/collections/{collection_name}/points/batch",
    status_code=status.HTTP_201_CREATED,
    summary="Batch добавление точек",
)
async def upsert_points_batch(
    collection_name: str,
    data: PointsBatchCreate,
    service: QdrantServiceDep,
) -> dict[str, int]:
    """
    Добавить несколько точек за один запрос.

    Args:
        collection_name: Имя коллекции.
        data: Список точек (до 1000).

    Returns:
        {"count": количество добавленных}

    Raises:
        404: Коллекция не найдена.
        422: Размерность вектора не соответствует.
    """
    count = await service.upsert_points_batch(collection_name, data.points)
    return {"count": count}


@router.get(
    "/collections/{collection_name}/points/{point_id}",
    response_model=PointResponse,
    summary="Получить точку",
)
async def get_point(
    collection_name: str,
    point_id: str,
    service: QdrantServiceDep,
    with_vector: bool = False,
) -> PointResponse:
    """
    Получить точку по ID.

    Args:
        collection_name: Имя коллекции.
        point_id: ID точки.
        with_vector: Включить вектор в ответ.

    Returns:
        Данные точки.

    Raises:
        404: Точка не найдена.
    """
    return await service.get_point(collection_name, point_id, with_vector)


@router.delete(
    "/collections/{collection_name}/points/{point_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить точку",
)
async def delete_point(
    collection_name: str,
    point_id: str,
    service: QdrantServiceDep,
) -> None:
    """
    Удалить точку из коллекции.

    Args:
        collection_name: Имя коллекции.
        point_id: ID точки.

    Raises:
        404: Точка не найдена.
    """
    await service.delete_point(collection_name, point_id)


# =============================================================================
# Search
# =============================================================================
@router.post(
    "/collections/{collection_name}/search",
    response_model=SearchResponse,
    summary="Векторный поиск",
)
async def search(
    collection_name: str,
    request: SearchRequest,
    service: QdrantServiceDep,
) -> SearchResponse:
    """
    Поиск ближайших соседей по вектору.

    Args:
        collection_name: Имя коллекции.
        request: Параметры поиска (вектор, лимит, фильтры).

    Returns:
        Список результатов с score.

    Raises:
        404: Коллекция не найдена.
        422: Размерность вектора не соответствует.
    """
    return await service.search(collection_name, request)
