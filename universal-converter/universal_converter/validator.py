from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from validataclass.validators import DataclassValidator

from .parkapi_models import RealtimeParkingSiteInput, StaticParkingSiteInput
from .types import InputKind


class ParkApiValidator:
    static_validator = DataclassValidator(StaticParkingSiteInput)
    realtime_validator = DataclassValidator(RealtimeParkingSiteInput)

    def validate(self, data: dict[str, Any], input_kind: InputKind, has_realtime_data_default: bool):
        if input_kind == InputKind.STATIC:
            data.setdefault('has_realtime_data', has_realtime_data_default)
            data.setdefault('static_data_updated_at', datetime.now(tz=timezone.utc).isoformat())
            return self.static_validator.validate(data)

        data.setdefault('realtime_data_updated_at', datetime.now(tz=timezone.utc).isoformat())
        return self.realtime_validator.validate(data)
