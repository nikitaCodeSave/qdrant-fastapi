"""
Pytest фикстуры.

Общие фикстуры для всех тестов:
- Тестовые настройки
- Async HTTP клиент
- Mock Qdrant клиент

Использование:
    async def test_example(client: AsyncClient):
        response = await client.get("/health")
        assert response.status_code == 200
"""

from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient

from src.config import Settings, get_settings
from src.main import app
from src.qdrant.client import QdrantClient, qdrant_client
from src.qdrant.dependencies import get_qdrant_client


# =============================================================================
# Settings Override
# =============================================================================
@pytest.fixture
def test_settings() -> Settings:
    """Тестовые настройки."""
    return Settings(
        project_name="Test Service",
        environment="development",
        qdrant_local_path="./test_qdrant_storage",
    )


# =============================================================================
# Mock Qdrant Client
# =============================================================================
@pytest.fixture
def mock_qdrant_client() -> MagicMock:
    """
    Mock Qdrant клиент.

    Возвращает MagicMock с настроенными async методами.
    """
    mock = MagicMock(spec=QdrantClient)

    # Health check
    mock.health_check = AsyncMock(
        return_value={
            "status": "healthy",
            "latency_ms": 1.5,
            "collections_count": 0,
        }
    )

    # Collections
    mock.list_collections = AsyncMock(return_value=[])
    mock.collection_exists = AsyncMock(return_value=False)
    mock.create_collection = AsyncMock(return_value=True)
    mock.delete_collection = AsyncMock(return_value=True)

    # Points
    mock.upsert_points = AsyncMock(return_value=1)
    mock.get_point = AsyncMock(return_value=None)
    mock.delete_points = AsyncMock(return_value=1)

    # Search
    mock.search = AsyncMock(return_value=[])

    return mock


# =============================================================================
# Async HTTP Client
# =============================================================================
@pytest.fixture
async def client(mock_qdrant_client: MagicMock) -> AsyncGenerator[AsyncClient, None]:
    """
    Async HTTP клиент для тестирования API.

    Переопределяет зависимости для изоляции от реального Qdrant.
    """
    # Override dependencies
    app.dependency_overrides[get_qdrant_client] = lambda: mock_qdrant_client

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    # Cleanup
    app.dependency_overrides.clear()


# =============================================================================
# Test Data Fixtures
# =============================================================================
@pytest.fixture
def sample_vector() -> list[float]:
    """Пример вектора размерности 1024."""
    return [0.1] * 1024


@pytest.fixture
def sample_point(sample_vector: list[float]) -> dict:
    """Пример точки для тестов."""
    return {
        "id": "test_point_1",
        "vector": sample_vector,
        "payload": {
            "text": "Test document content",
            "metadata": {"source": "test"},
        },
    }


@pytest.fixture
def sample_collection_create() -> dict:
    """Пример данных для создания коллекции."""
    return {
        "name": "test_collection",
        "vector_size": 1024,
        "distance": "Cosine",
    }
