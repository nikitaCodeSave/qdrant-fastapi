"""
Примеры использования Qdrant модуля в коде.

Показывает как работать с сервисом напрямую (без HTTP).
"""

import asyncio
from typing import Any

# Импорты из модуля qdrant
from qdrant.client import qdrant_client
from qdrant.service import QdrantService
from qdrant.schemas import (
    CollectionCreate,
    PointCreate,
    SearchRequest,
)
from qdrant.exceptions import (
    CollectionNotFoundError,
    CollectionAlreadyExistsError,
)


async def main():
    """Пример использования Qdrant модуля."""

    # =========================================================================
    # 1. Подключение
    # =========================================================================
    await qdrant_client.connect(host="localhost", port=6333)
    print("Connected to Qdrant")

    # Создаём сервис
    service = QdrantService(qdrant_client)

    # =========================================================================
    # 2. Создание коллекции
    # =========================================================================
    collection_name = "test_documents"
    vector_size = 384  # Например, для all-MiniLM-L6-v2

    try:
        collection = await service.create_collection(
            CollectionCreate(
                name=collection_name,
                vector_size=vector_size,
                distance="Cosine",
            )
        )
        print(f"Created collection: {collection.name}")
    except CollectionAlreadyExistsError:
        print(f"Collection {collection_name} already exists")
        collection = await service.get_collection(collection_name)

    # =========================================================================
    # 3. Добавление точек
    # =========================================================================
    # Симуляция embeddings (в реальности используйте sentence-transformers или OpenAI)
    import random
    def fake_embedding(text: str) -> list[float]:
        random.seed(hash(text) % 2**32)
        return [random.random() for _ in range(vector_size)]

    documents = [
        {"id": "doc_1", "text": "Python is a programming language", "category": "tech"},
        {"id": "doc_2", "text": "Machine learning is part of AI", "category": "tech"},
        {"id": "doc_3", "text": "Cooking pasta is easy", "category": "food"},
    ]

    for doc in documents:
        point = await service.upsert_point(
            collection_name=collection_name,
            point=PointCreate(
                id=doc["id"],
                vector=fake_embedding(doc["text"]),
                payload={"text": doc["text"], "category": doc["category"]},
            ),
        )
        print(f"Added point: {point.id}")

    # =========================================================================
    # 4. Batch добавление
    # =========================================================================
    batch_docs = [
        {"id": f"batch_{i}", "text": f"Batch document {i}", "category": "batch"}
        for i in range(5)
    ]

    points = [
        PointCreate(
            id=doc["id"],
            vector=fake_embedding(doc["text"]),
            payload={"text": doc["text"], "category": doc["category"]},
        )
        for doc in batch_docs
    ]

    count = await service.upsert_points_batch(collection_name, points)
    print(f"Batch added {count} points")

    # =========================================================================
    # 5. Векторный поиск
    # =========================================================================
    query_text = "What is programming?"
    query_vector = fake_embedding(query_text)

    results = await service.search(
        collection_name=collection_name,
        request=SearchRequest(
            vector=query_vector,
            limit=3,
            score_threshold=0.5,
        ),
    )

    print(f"\nSearch results for '{query_text}':")
    for r in results.results:
        print(f"  {r.id}: score={r.score:.3f}, text={r.payload.get('text', '')[:50]}")

    # =========================================================================
    # 6. Поиск с фильтром
    # =========================================================================
    results_filtered = await service.search(
        collection_name=collection_name,
        request=SearchRequest(
            vector=query_vector,
            limit=5,
            filter={"category": "tech"},  # Только tech категория
        ),
    )

    print(f"\nFiltered search (category=tech):")
    for r in results_filtered.results:
        print(f"  {r.id}: score={r.score:.3f}")

    # =========================================================================
    # 7. Получение точки
    # =========================================================================
    point = await service.get_point(collection_name, "doc_1", with_vector=False)
    print(f"\nPoint doc_1: {point.payload}")

    # =========================================================================
    # 8. Health check
    # =========================================================================
    health = await service.health_check()
    print(f"\nHealth: {health}")

    # =========================================================================
    # 9. Список коллекций
    # =========================================================================
    collections = await service.list_collections()
    print(f"\nCollections: {[c.name for c in collections.collections]}")

    # =========================================================================
    # 10. Удаление (опционально)
    # =========================================================================
    # await service.delete_point(collection_name, "doc_1")
    # await service.delete_collection(collection_name)

    # =========================================================================
    # Закрытие подключения
    # =========================================================================
    await qdrant_client.close()
    print("\nDone!")


if __name__ == "__main__":
    asyncio.run(main())
