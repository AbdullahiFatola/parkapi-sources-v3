from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import json

from .types import InputKind, MappingExceptionRule, MappingRule, SourceFormat


@dataclass
class AuthConfig:
    type: str = 'none'
    headers: dict[str, str] = field(default_factory=dict)
    query_params: dict[str, str] = field(default_factory=dict)


@dataclass
class PullConfig:
    url: str
    method: str = 'GET'
    timeout_seconds: int = 30
    auth: AuthConfig = field(default_factory=AuthConfig)


@dataclass
class MappingDocument:
    source_uid: str
    source_name: str
    source_format: SourceFormat
    input_kind: InputKind
    has_realtime_data: bool
    pull: PullConfig
    mapping_rules: list[MappingRule]
    sample_payload: str | dict[str, Any] | list[dict[str, Any]] | None = None
    exceptions: list[MappingExceptionRule] = field(default_factory=list)

    @classmethod
    def from_yaml(cls, content: str) -> 'MappingDocument':
        try:
            import yaml  # type: ignore

            raw = yaml.safe_load(content)
        except ModuleNotFoundError:
            raw = json.loads(content)
        rules = [MappingRule(**rule) for rule in raw['mapping_rules']]
        exceptions = [MappingExceptionRule(**rule) for rule in raw.get('exceptions', [])]
        auth_raw = raw.get('pull', {}).get('auth', {})
        pull_raw = raw['pull']
        return cls(
            source_uid=raw['source_uid'],
            source_name=raw['source_name'],
            source_format=SourceFormat(raw['source_format']),
            input_kind=InputKind(raw['input_kind']),
            has_realtime_data=raw.get('has_realtime_data', False),
            pull=PullConfig(
                url=pull_raw['url'],
                method=pull_raw.get('method', 'GET'),
                timeout_seconds=pull_raw.get('timeout_seconds', 30),
                auth=AuthConfig(
                    type=auth_raw.get('type', 'none'),
                    headers=auth_raw.get('headers', {}),
                    query_params=auth_raw.get('query_params', {}),
                ),
            ),
            mapping_rules=rules,
            sample_payload=raw.get('sample_payload'),
            exceptions=exceptions,
        )
