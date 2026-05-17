from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from typing import Any


class InputKind(str, Enum):
    STATIC = 'static'
    REALTIME = 'realtime'


class SourceFormat(str, Enum):
    JSON = 'json'
    GEOJSON = 'geojson'
    CSV = 'csv'
    XML = 'xml'
    EXCEL = 'excel'


Resolver = Callable[[dict[str, Any]], Any]


@dataclass(frozen=True)
class MappingRule:
    target_field: str
    source_field: str | None = None
    resolver: Resolver | None = None
    required: bool = False
    default: Any = None


@dataclass(frozen=True)
class MappingExceptionRule:
    target_field: str
    merge_from: list[str] | None = None
    exclude: bool = False
    separator: str = " "
