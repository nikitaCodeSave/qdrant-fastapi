"""
Dependency Injection для домена Qdrant.

Цепочка зависимостей:
    Request
        └── get_qdrant_service()
                └── get_qdrant_client()
                        └── qdrant_client (singleton)

Использование в роутере:
    @router.get("/collections")
    async def list_collections(
        service: QdrantService = Depends(get_qdrant_service),
    ):
        return await service.list_collections()
"""

from typing import Annotated

from fastapi import Depends

from src.qdrant.client import QdrantClient, qdrant_client
from src.qdrant.service import QdrantService


def get_qdrant_client() -> QdrantClient:
    """
    Dependency для получения Qdrant клиента.

    Возвращает singleton экземпляр.
    Клиент должен быть инициализирован в lifespan.

    Returns:
        QdrantClient singleton.
    """
    return qdrant_client


def get_qdrant_service(
    client: QdrantClient = Depends(get_qdrant_client),
) -> QdrantService:
    """
    Dependency для получения Qdrant сервиса.

    Создаёт новый экземпляр сервиса с инжектированным клиентом.

    Args:
        client: QdrantClient из get_qdrant_client().

    Returns:
        QdrantService с инжектированным клиентом.
    """
    return QdrantService(client)


# =============================================================================
# Type Aliases для удобства
# =============================================================================
# Используйте в роутерах для краткости:
#   async def endpoint(service: QdrantServiceDep):

QdrantClientDep = Annotated[QdrantClient, Depends(get_qdrant_client)]
QdrantServiceDep = Annotated[QdrantService, Depends(get_qdrant_service)]
