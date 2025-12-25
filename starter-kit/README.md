# Qdrant Starter Kit для FastAPI

Готовый модуль для интеграции векторной базы данных Qdrant в FastAPI проект.

## Возможности

- **Collections**: Создание, получение, удаление коллекций
- **Points CRUD**: Добавление, получение, удаление точек (векторов)
- **Batch операции**: До 1000 точек за один запрос
- **Векторный поиск**: query_points API с фильтрами по payload
- **Настройки HNSW**: Константы для тюнинга индекса
- **Health check**: Проверка состояния подключения

## Требования

- Python 3.11+
- FastAPI (любая версия с async поддержкой)
- qdrant-client >= 1.16.0

## Быстрый старт

### Шаг 1: Установка зависимости

```bash
pip install qdrant-client>=1.16.0
```

### Шаг 2: Копирование модуля

Скопируйте папку `qdrant/` в ваш проект:

```
your-project/
├── app/
│   ├── qdrant/       <-- скопируйте сюда
│   │   ├── __init__.py
│   │   ├── client.py
│   │   ├── constants.py
│   │   ├── dependencies.py
│   │   ├── exceptions.py
│   │   ├── router.py
│   │   ├── schemas.py
│   │   └── service.py
│   └── main.py
└── ...
```

### Шаг 3: Добавление настроек в config

Добавьте в ваш Settings класс (или .env файл):

```python
# config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # ... существующие настройки ...

    # Qdrant
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_api_key: str | None = None
    qdrant_local_path: str | None = None  # Для embedded режима

settings = Settings()
```

### Шаг 4: Настройка lifespan

```python
# main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from qdrant.client import qdrant_client

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: подключение к Qdrant
    await qdrant_client.connect(
        host=settings.qdrant_host,
        port=settings.qdrant_port,
        api_key=settings.qdrant_api_key,
    )
    yield
    # Shutdown: закрытие подключения
    await qdrant_client.close()

app = FastAPI(lifespan=lifespan)
```

### Шаг 5: Подключение роутера

```python
# main.py
from qdrant import router as qdrant_router

app.include_router(qdrant_router, prefix="/api/v1")
```

### Шаг 6: Добавление exception handler

```python
# main.py
from fastapi.responses import JSONResponse
from qdrant.exceptions import DomainError

@app.exception_handler(DomainError)
async def domain_error_handler(request, exc: DomainError):
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_dict(),
    )
```

### Шаг 7: Запуск Qdrant

**Docker:**
```bash
docker run -p 6333:6333 qdrant/qdrant
```

**Embedded (без Docker):**
```bash
# В .env
QDRANT_LOCAL_PATH=./qdrant_storage
```

## API Endpoints

| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET | `/qdrant/collections` | Список коллекций |
| GET | `/qdrant/collections/{name}` | Информация о коллекции |
| POST | `/qdrant/collections` | Создать коллекцию |
| DELETE | `/qdrant/collections/{name}` | Удалить коллекцию |
| POST | `/qdrant/collections/{name}/points` | Добавить точку |
| POST | `/qdrant/collections/{name}/points/batch` | Batch добавление |
| GET | `/qdrant/collections/{name}/points/{id}` | Получить точку |
| DELETE | `/qdrant/collections/{name}/points/{id}` | Удалить точку |
| POST | `/qdrant/collections/{name}/search` | Векторный поиск |

## Примеры использования

### Создание коллекции

```bash
curl -X POST http://localhost:8000/api/v1/qdrant/collections \
  -H "Content-Type: application/json" \
  -d '{
    "name": "documents",
    "vector_size": 1024,
    "distance": "Cosine"
  }'
```

### Добавление точки

```bash
curl -X POST http://localhost:8000/api/v1/qdrant/collections/documents/points \
  -H "Content-Type: application/json" \
  -d '{
    "id": "doc_001",
    "vector": [0.1, 0.2, ...],
    "payload": {
      "text": "Содержимое документа",
      "category": "tech"
    }
  }'
```

### Batch добавление

```bash
curl -X POST http://localhost:8000/api/v1/qdrant/collections/documents/points/batch \
  -H "Content-Type: application/json" \
  -d '{
    "points": [
      {"id": "doc_001", "vector": [...], "payload": {...}},
      {"id": "doc_002", "vector": [...], "payload": {...}}
    ]
  }'
```

### Векторный поиск

```bash
curl -X POST http://localhost:8000/api/v1/qdrant/collections/documents/search \
  -H "Content-Type: application/json" \
  -d '{
    "vector": [0.1, 0.2, ...],
    "limit": 10,
    "score_threshold": 0.7,
    "filter": {"category": "tech"}
  }'
```

## Настройки HNSW индекса

Параметры находятся в `constants.py`:

```python
class HNSWDefaults:
    M = 16              # Связи на вершину (больше = точнее, больше памяти)
    EF_CONSTRUCT = 100  # Качество построения индекса
    FULL_SCAN_THRESHOLD = 10000  # Порог для полного скана
```

Для создания коллекции с кастомными HNSW параметрами используйте Qdrant API напрямую.

## Режимы подключения

### Server Mode (Docker)
```python
await qdrant_client.connect(host="localhost", port=6333)
```

### Cloud Mode (Qdrant Cloud)
```python
await qdrant_client.connect(
    url="https://xxx.cloud.qdrant.io:6333",
    api_key="your-api-key"
)
```

### Local Mode (Embedded)
```python
await qdrant_client.connect(path="./qdrant_storage")
```

## Структура файлов

```
qdrant/
├── __init__.py       # Экспорты модуля
├── client.py         # AsyncQdrantClient singleton
├── constants.py      # Лимиты, Distance, HNSW defaults
├── dependencies.py   # FastAPI DI
├── exceptions.py     # Доменные исключения
├── router.py         # HTTP endpoints
├── schemas.py        # Pydantic DTOs
└── service.py        # Бизнес-логика
```

## Исключения

| Исключение | HTTP код | Описание |
|------------|----------|----------|
| `CollectionNotFoundError` | 404 | Коллекция не найдена |
| `CollectionAlreadyExistsError` | 409 | Коллекция уже существует |
| `PointNotFoundError` | 404 | Точка не найдена |
| `VectorSizeMismatchError` | 422 | Размерность вектора не совпадает |
| `QdrantConnectionError` | 503 | Ошибка подключения |

## Лицензия

MIT
