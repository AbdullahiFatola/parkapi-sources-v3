from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from parkapi_sources.exceptions import ImportParkingSiteException

from .mapping_document import MappingDocument
from .parsers import SourceParser
from .parkapi_models import SourceInfo
from .source_client import SourceClient
from .transformer import RecordTransformer
from .types import InputKind, MappingRule, SourceFormat
from .validator import ParkApiValidator


@dataclass
class ConversionError:
    source_uid: str
    message: str
    parking_site_uid: str | None = None
    data: dict[str, Any] | None = None


class UniversalConverter:
    def __init__(self, source_info: SourceInfo):
        self.source_info = source_info
        self.client = SourceClient()
        self.parser = SourceParser()
        self.transformer = RecordTransformer()
        self.validator = ParkApiValidator()

    def convert(self, payload: str | bytes | list[dict[str, Any]] | dict[str, Any], source_format: SourceFormat, mapping_rules: list[MappingRule], input_kind: InputKind):
        rows = self.parser.parse(source_format=source_format, payload=payload)
        return self._convert_rows(rows=rows, mapping_rules=mapping_rules, input_kind=input_kind, exception_rules=None)

    def convert_from_mapping_document(self, mapping_document: MappingDocument, use_sample_data: bool = False):
        payload = (
            SourceClient.parse_sample(mapping_document.sample_payload)
            if use_sample_data
            else self.client.fetch(mapping_document.pull)
        )
        rows = self.parser.parse(source_format=mapping_document.source_format, payload=payload)
        return self._convert_rows(
            rows=rows,
            mapping_rules=mapping_document.mapping_rules,
            input_kind=mapping_document.input_kind,
            exception_rules=mapping_document.exceptions,
        )

    def _convert_rows(self, rows: list[dict[str, Any]], mapping_rules: list[MappingRule], input_kind: InputKind, exception_rules=None):
        outputs, errors = [], []
        for row in rows:
            transformed: dict[str, Any] = {}
            try:
                transformed = self.transformer.transform(row, mapping_rules, exception_rules=exception_rules)
                outputs.append(self.validator.validate(transformed, input_kind=input_kind, has_realtime_data_default=self.source_info.has_realtime_data or False))
            except Exception as exception:  # noqa: BLE001
                wrapped = ImportParkingSiteException(
                    source_uid=self.source_info.uid,
                    message=str(exception),
                    parking_site_uid=transformed.get('uid') if isinstance(transformed.get('uid'), str) else None,
                    data=row,
                )
                errors.append(ConversionError(source_uid=wrapped.source_uid, message=wrapped.message, parking_site_uid=wrapped.parking_site_uid, data=wrapped.data))
        return outputs, errors
