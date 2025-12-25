# Qdrant Client (Data Access Layer)

## Обзор

`QdrantClient` — обёртка над `AsyncQdrantClient` из официальной библиотеки `qdrant-client`. Реализует паттерн **Singleton** и предоставляет:

- Управление жизненным циклом подключения
- Health check
- CRUD операции с коллекциями и точками
- Векторный поиск

**Файл:** `src/qdrant/client.py`

## Принципы

1. **Singleton**: один клиент на всё приложение
2. **Только Data Access**: никакой бизнес-логики
3. **Lifecycle через Lifespan**: connect/close в main.py
4. **Выбрасывает доменные исключения**: для ошибок подключения и отсутствующих ресурсов

---

## Singleton Pattern

```python
class QdrantClient:
    _instance: QdrantClient | None = None
    _client: AsyncQdrantClient | None = None
    _initialized: bool = False

    def __new__(cls) -> QdrantClient:
        """Возвращает существующий экземпляр или создаёт новый."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
```

### Глобальный экземпляр

```python
# src/qdrant/client.py
qdrant_client = QdrantClient()

# Использование
from src.qdrant.client import qdrant_client

await qdrant_client.connect()
collections = await qdrant_client.list_collections()
```

---

## Lifecycle Management

### Подключение

```python
async def connect(self) -> None:
    """Инициализация подключения к Qdrant."""
    if self._initialized:
        return

    client_kwargs = settings.get_qdrant_client_kwargs()
    mode = "local" if settings.is_local_mode else "server"

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
```

### Закрытие

```python
async def close(self) -> None:
    """Закрытие подключения."""
    if self._client is not None:
        logger.info("Closing Qdrant connection")
        await self._client.close()
        self._client = None
        self._initialized = False
```

### Интеграция с Lifespan

```python
# src/main.py
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # STARTUP
    await qdrant_client.connect()
    yield
    # SHUTDOWN
    await qdrant_client.close()
```

---

## Health Check

```python
async def health_check(self) -> dict[str, Any]:
    """Проверка состояния подключения."""
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
```

**Пример ответа:**

```json
{
  "status": "healthy",
  "latency_ms": 2.5,
  "collections_count": 3
}
```

---

## API методов

### Collections

#### list_collections

```python
async def list_collections(self) -> list[str]:
    """Получить список имён коллекций."""
    result = await self.client.get_collections()
    return [c.name for c in result.collections]
```

#### collection_exists

```python
async def collection_exists(self, name: str) -> bool:
    """Проверить существование коллекции."""
    return await self.client.collection_exists(name)
```

#### get_collection_info

```python
async def get_collection_info(self, name: str) -> models.CollectionInfo:
    """Получить информацию о коллекции."""
    if not await self.collection_exists(name):
        raise CollectionNotFoundError(
            f"Collection '{name}' not found",
            details={"collection": name},
        )
    return await self.client.get_collection(name)
```

#### create_collection

```python
async def create_collection(
    self,
    name: str,
    vector_size: int,
    distance: str = "Cosine",
    on_disk: bool = False,
) -> bool:
    """Создать коллекцию."""
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
    return True
```

#### delete_collection

```python
async def delete_collection(self, name: str) -> bool:
    """Удалить коллекцию."""
    if not await self.collection_exists(name):
        raise CollectionNotFoundError(
            f"Collection '{name}' not found",
            details={"collection": name},
        )
    await self.client.delete_collection(name)
    return True
```

---

### Points

#### upsert_points

```python
async def upsert_points(
    self,
    collection_name: str,
    points: list[models.PointStruct],
) -> int:
    """Добавить или обновить точки."""
    await self.client.upsert(
        collection_name=collection_name,
        points=points,
        wait=True,  # Ожидание подтверждения
    )
    return len(points)
```

#### get_point

```python
async def get_point(
    self,
    collection_name: str,
    point_id: str | int,
    with_vector: bool = False,
) -> models.Record | None:
    """Получить точку по ID."""
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
```

#### delete_points

```python
async def delete_points(
    self,
    collection_name: str,
    point_ids: list[str | int],
) -> int:
    """Удалить точки по ID."""
    await self.client.delete(
        collection_name=collection_name,
        points_selector=models.PointIdsList(points=point_ids),
        wait=True,
    )
    return len(point_ids)
```

---

### Search

```python
async def search(
    self,
    collection_name: str,
    vector: list[float],
    limit: int = 10,
    score_threshold: float | None = None,
    filter_: dict | None = None,
    with_payload: bool = True,
    with_vector: bool = False,
) -> list[models.ScoredPoint]:
    """Векторный поиск."""
    qdrant_filter = None
    if filter_:
        qdrant_filter = self._build_filter(filter_)

    return await self.client.search(
        collection_name=collection_name,
        query_vector=vector,
        limit=limit,
        score_threshold=score_threshold,
        query_filter=qdrant_filter,
        with_payload=with_payload,
        with_vectors=with_vector,
    )
```

---

## Построение фильтров

```python
def _build_filter(self, filter_dict: dict) -> models.Filter:
    """Конвертирует dict в Qdrant Filter."""
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
```

**Пример:**

```python
filter_dict = {"source": "manual.pdf", "language": "ru"}

# Результат: Filter(must=[
#     FieldCondition(key="source", match=MatchValue(value="manual.pdf")),
#     FieldCondition(key="language", match=MatchValue(value="ru")),
# ])
```

---

## Property client

```python
@property
def client(self) -> AsyncQdrantClient:
    """Получить внутренний клиент."""
    if self._client is None:
        raise QdrantConnectionError("Qdrant client not initialized")
    return self._client
```

---

## Режимы подключения

### Server Mode

```python
# settings.get_qdrant_client_kwargs() возвращает:
{
    "host": "localhost",
    "port": 6333,
    "grpc_port": 6334,
    "api_key": None,
    "prefer_grpc": True,
    "timeout": 30.0,
    "https": False,
}
```

### Local Mode (Embedded)

```python
# settings.get_qdrant_client_kwargs() возвращает:
{
    "path": "./qdrant_storage"
}
```

---

## Обработка ошибок

Client выбрасывает доменные исключения:

| Ситуация | Исключение |
|----------|------------|
| Коллекция не найдена | `CollectionNotFoundError` |
| Коллекция уже существует | `CollectionAlreadyExistsError` |
| Ошибка подключения | `QdrantConnectionError` |

---

## Тестирование

При тестировании клиент мокается:

```python
# tests/conftest.py
@pytest.fixture
def mock_qdrant_client() -> MagicMock:
    mock = MagicMock(spec=QdrantClient)
    mock.health_check = AsyncMock(return_value={...})
    mock.list_collections = AsyncMock(return_value=[])
    # ...
    return mock

@pytest.fixture
async def client(mock_qdrant_client):
    app.dependency_overrides[get_qdrant_client] = lambda: mock_qdrant_client
    # ...
```

## Следующие разделы

- [Сервисный слой](09_сервисный_слой.md) — бизнес-логика
- [Тестирование](10_тестирование.md) — как тестировать
