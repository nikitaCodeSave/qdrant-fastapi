# API Reference

## Базовый URL

```
http://localhost:8000/api/v1
```

Префикс настраивается через `API_PREFIX` в конфигурации.

## Аутентификация

В текущей версии API не требует аутентификации. Для production рекомендуется добавить API ключи или OAuth2.

---

## Monitoring

### Health Check

Проверка состояния сервиса и зависимостей.

```http
GET /health
```

**Response 200 OK:**

```json
{
  "status": "healthy",
  "version": "0.1.0",
  "timestamp": "2025-01-01T12:00:00Z",
  "services": {
    "qdrant": {
      "status": "healthy",
      "latency_ms": 2.5,
      "error": null
    }
  }
}
```

**Статусы:**
- `healthy` — все сервисы работают
- `degraded` — некоторые сервисы недоступны
- `unhealthy` — критические сервисы недоступны

---

## Collections

### Список коллекций

```http
GET /api/v1/qdrant/collections
```

**Response 200 OK:**

```json
{
  "collections": [
    {
      "name": "documents",
      "vectors_count": 1500,
      "points_count": 1500,
      "status": "green",
      "vector_size": 1024,
      "distance": "Cosine"
    }
  ],
  "total": 1
}
```

**cURL:**

```bash
curl http://localhost:8000/api/v1/qdrant/collections
```

---

### Информация о коллекции

```http
GET /api/v1/qdrant/collections/{name}
```

**Path Parameters:**

| Параметр | Тип | Описание |
|----------|-----|----------|
| `name` | string | Имя коллекции |

**Response 200 OK:**

```json
{
  "name": "documents",
  "vectors_count": 1500,
  "points_count": 1500,
  "status": "green",
  "vector_size": 1024,
  "distance": "Cosine"
}
```

**Response 404 Not Found:**

```json
{
  "error": "collection_not_found",
  "message": "Collection 'documents' not found",
  "details": {"collection": "documents"}
}
```

**cURL:**

```bash
curl http://localhost:8000/api/v1/qdrant/collections/documents
```

---

### Создание коллекции

```http
POST /api/v1/qdrant/collections
```

**Request Body:**

```json
{
  "name": "documents",
  "vector_size": 1024,
  "distance": "Cosine",
  "on_disk": false
}
```

| Поле | Тип | Обязательно | Описание |
|------|-----|-------------|----------|
| `name` | string | Да | Имя коллекции (1-255 символов) |
| `vector_size` | int | Да | Размерность векторов (1-65536) |
| `distance` | string | Нет | Метрика: `Cosine`, `Euclid`, `Dot`. Default: `Cosine` |
| `on_disk` | bool | Нет | Хранить векторы на диске. Default: `false` |

**Response 201 Created:**

```json
{
  "name": "documents",
  "vectors_count": 0,
  "points_count": 0,
  "status": "green",
  "vector_size": 1024,
  "distance": "Cosine"
}
```

**Response 409 Conflict:**

```json
{
  "error": "collection_already_exists",
  "message": "Collection 'documents' already exists",
  "details": {"collection": "documents"}
}
```

**cURL:**

```bash
curl -X POST http://localhost:8000/api/v1/qdrant/collections \
  -H "Content-Type: application/json" \
  -d '{"name": "documents", "vector_size": 1024, "distance": "Cosine"}'
```

---

### Удаление коллекции

```http
DELETE /api/v1/qdrant/collections/{name}
```

**Path Parameters:**

| Параметр | Тип | Описание |
|----------|-----|----------|
| `name` | string | Имя коллекции |

**Response 204 No Content**

**Response 404 Not Found:**

```json
{
  "error": "collection_not_found",
  "message": "Collection 'documents' not found"
}
```

**cURL:**

```bash
curl -X DELETE http://localhost:8000/api/v1/qdrant/collections/documents
```

---

## Points (Документы)

### Добавление точки

```http
POST /api/v1/qdrant/collections/{collection_name}/points
```

**Path Parameters:**

| Параметр | Тип | Описание |
|----------|-----|----------|
| `collection_name` | string | Имя коллекции |

**Request Body:**

```json
{
  "id": "doc_123",
  "vector": [0.1, 0.2, 0.3, ...],
  "payload": {
    "text": "Содержимое документа...",
    "metadata": {
      "source": "manual.pdf",
      "page": 5
    }
  }
}
```

| Поле | Тип | Обязательно | Описание |
|------|-----|-------------|----------|
| `id` | string \| int | Да | Уникальный ID точки |
| `vector` | float[] | Да | Вектор embedding |
| `payload` | object | Нет | Метаданные документа |

**Response 201 Created:**

```json
{
  "id": "doc_123",
  "vector": [0.1, 0.2, 0.3, ...],
  "payload": {
    "text": "Содержимое документа...",
    "metadata": {"source": "manual.pdf", "page": 5}
  }
}
```

**Response 422 Unprocessable Entity:**

```json
{
  "error": "vector_size_mismatch",
  "message": "Expected 1024, got 512",
  "details": {"expected": 1024, "got": 512}
}
```

**cURL:**

```bash
curl -X POST http://localhost:8000/api/v1/qdrant/collections/documents/points \
  -H "Content-Type: application/json" \
  -d '{
    "id": "doc_123",
    "vector": [0.1, 0.2, ...],
    "payload": {"text": "Hello world"}
  }'
```

---

### Batch добавление точек

```http
POST /api/v1/qdrant/collections/{collection_name}/points/batch
```

**Request Body:**

```json
{
  "points": [
    {
      "id": "doc_1",
      "vector": [0.1, 0.2, ...],
      "payload": {"text": "Document 1"}
    },
    {
      "id": "doc_2",
      "vector": [0.3, 0.4, ...],
      "payload": {"text": "Document 2"}
    }
  ]
}
```

| Поле | Тип | Обязательно | Описание |
|------|-----|-------------|----------|
| `points` | PointCreate[] | Да | Массив точек (1-1000) |

**Response 201 Created:**

```json
{
  "count": 2
}
```

**cURL:**

```bash
curl -X POST http://localhost:8000/api/v1/qdrant/collections/documents/points/batch \
  -H "Content-Type: application/json" \
  -d '{
    "points": [
      {"id": "doc_1", "vector": [...], "payload": {}},
      {"id": "doc_2", "vector": [...], "payload": {}}
    ]
  }'
```

---

### Получение точки

```http
GET /api/v1/qdrant/collections/{collection_name}/points/{point_id}
```

**Path Parameters:**

| Параметр | Тип | Описание |
|----------|-----|----------|
| `collection_name` | string | Имя коллекции |
| `point_id` | string | ID точки |

**Query Parameters:**

| Параметр | Тип | По умолчанию | Описание |
|----------|-----|--------------|----------|
| `with_vector` | bool | false | Включить вектор в ответ |

**Response 200 OK:**

```json
{
  "id": "doc_123",
  "vector": null,
  "payload": {
    "text": "Содержимое документа..."
  }
}
```

**Response 404 Not Found:**

```json
{
  "error": "point_not_found",
  "message": "Point 'doc_123' not found"
}
```

**cURL:**

```bash
curl "http://localhost:8000/api/v1/qdrant/collections/documents/points/doc_123?with_vector=true"
```

---

### Удаление точки

```http
DELETE /api/v1/qdrant/collections/{collection_name}/points/{point_id}
```

**Response 204 No Content**

**Response 404 Not Found:**

```json
{
  "error": "point_not_found",
  "message": "Point 'doc_123' not found"
}
```

**cURL:**

```bash
curl -X DELETE http://localhost:8000/api/v1/qdrant/collections/documents/points/doc_123
```

---

## Search

### Векторный поиск

```http
POST /api/v1/qdrant/collections/{collection_name}/search
```

**Request Body:**

```json
{
  "vector": [0.1, 0.2, 0.3, ...],
  "limit": 10,
  "score_threshold": 0.7,
  "with_payload": true,
  "with_vector": false,
  "filter": {
    "source": "manual.pdf"
  }
}
```

| Поле | Тип | Обязательно | По умолчанию | Описание |
|------|-----|-------------|--------------|----------|
| `vector` | float[] | Да | - | Вектор запроса |
| `limit` | int | Нет | 10 | Количество результатов (1-100) |
| `score_threshold` | float | Нет | null | Минимальный score (0.0-1.0) |
| `with_payload` | bool | Нет | true | Включить payload |
| `with_vector` | bool | Нет | false | Включить вектор |
| `filter` | object | Нет | null | Фильтр по полям payload |

**Response 200 OK:**

```json
{
  "results": [
    {
      "id": "doc_123",
      "score": 0.95,
      "payload": {
        "text": "Релевантный документ...",
        "source": "manual.pdf"
      },
      "vector": null
    },
    {
      "id": "doc_456",
      "score": 0.87,
      "payload": {
        "text": "Другой документ..."
      },
      "vector": null
    }
  ],
  "total": 2,
  "limit": 10,
  "query_time_ms": 3.45
}
```

**cURL:**

```bash
curl -X POST http://localhost:8000/api/v1/qdrant/collections/documents/search \
  -H "Content-Type: application/json" \
  -d '{
    "vector": [0.1, 0.2, ...],
    "limit": 5,
    "score_threshold": 0.7
  }'
```

---

## Фильтрация при поиске

### Простые фильтры

Фильтрация по точному значению поля:

```json
{
  "vector": [...],
  "filter": {
    "source": "manual.pdf"
  }
}
```

### Множественные условия

Все условия объединяются через AND:

```json
{
  "vector": [...],
  "filter": {
    "source": "manual.pdf",
    "page": 5,
    "language": "ru"
  }
}
```

---

## HTTP статусы

| Код | Описание |
|-----|----------|
| 200 | Успешный запрос |
| 201 | Ресурс создан |
| 204 | Успешное удаление |
| 400 | Ошибка в запросе |
| 404 | Ресурс не найден |
| 409 | Конфликт (ресурс уже существует) |
| 422 | Ошибка валидации |
| 503 | Сервис недоступен |

---

## Rate Limiting

В текущей версии rate limiting не реализован. Для production рекомендуется добавить через reverse proxy (nginx) или middleware.

---

## Версионирование

API версионируется через URL prefix: `/api/v1/`. При breaking changes будет создана новая версия `/api/v2/`.

## Следующие разделы

- [Схемы данных](06_схемы_данных.md) — Pydantic модели
- [Обработка ошибок](07_обработка_ошибок.md) — коды и форматы ошибок
