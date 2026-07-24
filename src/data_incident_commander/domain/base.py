"""Shared strict model and serialization utilities."""

from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping

from pydantic import BaseModel, ConfigDict


class StrictModel(BaseModel):
    """Immutable, strict, public-safe domain model."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        strict=True,
        use_enum_values=False,
    )


def utc_datetime(value: datetime) -> datetime:
    """Require an aware timestamp and normalize it to UTC."""

    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("timestamp must be timezone-aware")
    return value.astimezone(timezone.utc)


def freeze_json_value(value: Any, *, path: str = "$") -> Any:
    """Validate and deeply freeze a canonical JSON-compatible value."""

    if value is None or isinstance(value, bool | int | str):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError(f"{path} contains a non-finite float")
        return value
    if isinstance(value, Mapping):
        frozen: dict[str, Any] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise ValueError(f"{path} contains a non-string mapping key")
            frozen[key] = freeze_json_value(item, path=f"{path}.{key}")
        return MappingProxyType(frozen)
    if isinstance(value, list | tuple):
        return tuple(
            freeze_json_value(item, path=f"{path}[{index}]")
            for index, item in enumerate(value)
        )
    raise ValueError(f"{path} contains unsupported JSON value {type(value).__name__}")


def thaw_json_value(value: Any) -> Any:
    """Convert a frozen JSON value back to ordinary JSON containers."""

    if isinstance(value, Mapping):
        return {key: thaw_json_value(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [thaw_json_value(item) for item in value]
    return value


def freeze_mapping(value: Mapping[str, Any]) -> Mapping[str, Any]:
    frozen = freeze_json_value(value)
    if not isinstance(frozen, Mapping):
        raise ValueError("expected a string-keyed mapping")
    return frozen


def thaw_mapping(value: Mapping[str, Any]) -> dict[str, Any]:
    thawed = thaw_json_value(value)
    if not isinstance(thawed, dict):
        raise TypeError("expected a frozen mapping")
    return thawed


def canonical_json(model: BaseModel) -> str:
    """Serialize a model predictably for hashing, comparison, and tests."""

    def default(value: Any) -> Any:
        if isinstance(value, datetime):
            return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
        if isinstance(value, Enum):
            return value.value
        if isinstance(value, BaseModel):
            return value.model_dump(mode="python")
        raise TypeError(f"Unsupported JSON value: {type(value).__name__}")

    return json.dumps(
        model.model_dump(mode="python"),
        default=default,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
