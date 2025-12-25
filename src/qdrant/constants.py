"""
Константы домена Qdrant.

Единый источник истины для:
- Ограничений и лимитов
- Значений по умолчанию
- Enum-подобных констант

Используется в schemas.py и service.py для консистентности.
"""

from typing import Final


# =============================================================================
# Collection Settings
# =============================================================================
class Distance:
    """Метрики расстояния для векторного поиска."""

    COSINE: Final[str] = "Cosine"
    EUCLID: Final[str] = "Euclid"
    DOT: Final[str] = "Dot"

    ALL: Final[tuple[str, ...]] = (COSINE, EUCLID, DOT)


# =============================================================================
# Limits
# =============================================================================
# Имена коллекций
MAX_COLLECTION_NAME_LENGTH: Final[int] = 255
MIN_COLLECTION_NAME_LENGTH: Final[int] = 1

# Размерность векторов
MIN_VECTOR_SIZE: Final[int] = 1
MAX_VECTOR_SIZE: Final[int] = 65536

# Поиск
DEFAULT_SEARCH_LIMIT: Final[int] = 10
MAX_SEARCH_LIMIT: Final[int] = 100
MIN_SCORE_THRESHOLD: Final[float] = 0.0
MAX_SCORE_THRESHOLD: Final[float] = 1.0

# Batch операции
DEFAULT_BATCH_SIZE: Final[int] = 100
MAX_BATCH_SIZE: Final[int] = 1000

# Payload
MAX_PAYLOAD_KEY_LENGTH: Final[int] = 255
MAX_TEXT_FIELD_LENGTH: Final[int] = 65536


# =============================================================================
# HNSW Index Defaults
# =============================================================================
class HNSWDefaults:
    """
    Параметры HNSW индекса по умолчанию.

    m: Количество связей на вершину (больше = точнее, но больше памяти)
    ef_construct: Размер динамического списка при построении
    full_scan_threshold: Порог для перехода на полный скан
    """

    M: Final[int] = 16
    EF_CONSTRUCT: Final[int] = 100
    FULL_SCAN_THRESHOLD: Final[int] = 10000


# =============================================================================
# Quantization Defaults
# =============================================================================
class QuantizationDefaults:
    """Параметры квантизации для экономии памяти."""

    ALWAYS_RAM: Final[bool] = True
    RESCORE: Final[bool] = True


# =============================================================================
# Named Vectors (для гибридного поиска)
# =============================================================================
class VectorNames:
    """Имена векторов для гибридного поиска."""

    DENSE: Final[str] = "dense"
    SPARSE: Final[str] = "sparse"


# =============================================================================
# Payload Field Names
# =============================================================================
class PayloadFields:
    """Стандартные имена полей в payload."""

    TEXT: Final[str] = "text"
    DOCUMENT_ID: Final[str] = "document_id"
    CHUNK_INDEX: Final[str] = "chunk_index"
    TOTAL_CHUNKS: Final[str] = "total_chunks"
    METADATA: Final[str] = "metadata"
    CREATED_AT: Final[str] = "created_at"
    FILE_HASH: Final[str] = "file_hash"
