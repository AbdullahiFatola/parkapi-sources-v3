from __future__ import annotations

import json
from typing import Any

import requests

from .mapping_document import PullConfig


class SourceClient:
    def fetch(self, pull: PullConfig) -> str | bytes | dict[str, Any] | list[dict[str, Any]]:
        response = requests.request(
            method=pull.method,
            url=pull.url,
            headers=pull.auth.headers,
            params=pull.auth.query_params,
            timeout=pull.timeout_seconds,
        )
        response.raise_for_status()

        content_type = response.headers.get('Content-Type', '')
        if 'application/json' in content_type:
            return response.json()
        return response.text

    @staticmethod
    def parse_sample(sample_payload: Any) -> str | bytes | dict[str, Any] | list[dict[str, Any]]:
        if isinstance(sample_payload, (dict, list)):
            return sample_payload
        if isinstance(sample_payload, str):
            try:
                return json.loads(sample_payload)
            except json.JSONDecodeError:
                return sample_payload
        return sample_payload
