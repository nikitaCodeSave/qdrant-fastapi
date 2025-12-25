"""
Тесты роутера Qdrant.

Интеграционные тесты API endpoints.
Используют mock Qdrant клиент из conftest.py.
"""

import pytest
from httpx import AsyncClient


class TestHealthEndpoint:
    """Тесты health check."""

    async def test_health_returns_200(self, client: AsyncClient) -> None:
        """Health endpoint возвращает 200."""
        response = await client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "qdrant" in data["services"]


class TestCollectionsEndpoints:
    """Тесты endpoints коллекций."""

    async def test_list_collections_empty(self, client: AsyncClient) -> None:
        """Пустой список коллекций."""
        response = await client.get("/api/v1/qdrant/collections")

        assert response.status_code == 200
        data = response.json()
        assert data["collections"] == []
        assert data["total"] == 0

    async def test_create_collection_success(
        self,
        client: AsyncClient,
        sample_collection_create: dict,
        mock_qdrant_client,
    ) -> None:
        """Успешное создание коллекции."""
        # Настраиваем mock для get_collection_info
        from qdrant_client import models

        mock_info = models.CollectionInfo(
            status=models.CollectionStatus.GREEN,
            vectors_count=0,
            points_count=0,
            config=models.CollectionConfig(
                params=models.CollectionParams(
                    vectors=models.VectorParams(
                        size=1024,
                        distance=models.Distance.COSINE,
                    ),
                ),
            ),
        )
        mock_qdrant_client.get_collection_info.return_value = mock_info
        mock_qdrant_client.collection_exists.return_value = False

        response = await client.post(
            "/api/v1/qdrant/collections",
            json=sample_collection_create,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == sample_collection_create["name"]

    async def test_create_collection_validation_error(
        self,
        client: AsyncClient,
    ) -> None:
        """Ошибка валидации при создании коллекции."""
        response = await client.post(
            "/api/v1/qdrant/collections",
            json={"name": "", "vector_size": 0},  # Невалидные данные
        )

        assert response.status_code == 422


class TestSearchEndpoints:
    """Тесты endpoints поиска."""

    async def test_search_validation_error(
        self,
        client: AsyncClient,
    ) -> None:
        """Ошибка валидации при поиске."""
        response = await client.post(
            "/api/v1/qdrant/collections/test/search",
            json={"vector": []},  # Пустой вектор
        )

        assert response.status_code == 422
