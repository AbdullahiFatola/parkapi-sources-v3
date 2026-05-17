from __future__ import annotations

from typing import Any

from .types import MappingExceptionRule, MappingRule


class RecordTransformer:
    def transform(
        self,
        item: dict[str, Any],
        mapping_rules: list[MappingRule],
        exception_rules: list[MappingExceptionRule] | None = None,
    ) -> dict[str, Any]:
        transformed: dict[str, Any] = {}
        for rule in mapping_rules:
            value = rule.default
            if rule.resolver is not None:
                value = rule.resolver(item)
            elif rule.source_field and rule.source_field in item:
                value = item[rule.source_field]
            if rule.required and value is None:
                raise ValueError(f"Required field '{rule.target_field}' is missing")
            transformed[rule.target_field] = value

        for exception_rule in exception_rules or []:
            if exception_rule.exclude:
                transformed.pop(exception_rule.target_field, None)
                continue

            if exception_rule.merge_from:
                if len(exception_rule.merge_from) > 2:
                    raise ValueError(
                        f"Exception merge for '{exception_rule.target_field}' supports max 2 attributes",
                    )
                merge_values = [str(item.get(field)).strip() for field in exception_rule.merge_from if item.get(field) is not None]
                transformed[exception_rule.target_field] = exception_rule.separator.join(merge_values) if merge_values else None

        return transformed
