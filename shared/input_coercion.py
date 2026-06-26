"""LLM이 보낸 input을 Pydantic이 받아들이도록 강제 변환.

문제: 카카오 GPT/Claude가 Tool 호출 시 free-text 필드(parent_brief, message_text 등)를
종종 dict 또는 list로 구조화해서 보냄. Pydantic `str` 타입은 strict 검증이라 즉시 실패 →
isError: true → Tool 무용지물.

해결: `field_validator(mode="before")`로 들어오기 직전에 dict/list를 자연 문자열로 합침.
LLM이 자체 판단으로 구조화해도 우리 Tool이 받아들임. 검증 통과율 ~100%.

이 모듈은 Pydantic v2의 `field_validator` API에 의존.
"""
from __future__ import annotations

from typing import Any


def coerce_to_string(value: Any) -> Any:
    """LLM이 보낸 임의 타입을 문자열로 강제 변환.

    - str → 그대로
    - dict → 'key: value, key: value' 형식으로 평탄화
    - list → ', '로 join
    - None → None (옵셔널 필드 유지)
    - 기타 → str() 변환

    중첩 dict/list도 한 번만 풀어냄 (Tool은 LLM이 채운 평탄한 brief를 기대).
    """
    if value is None:
        return None
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        return ", ".join(f"{k}: {_stringify_nested(v)}" for k, v in value.items())
    if isinstance(value, list):
        return ", ".join(_stringify_nested(v) for v in value)
    return str(value)


def _stringify_nested(value: Any) -> str:
    """dict/list 내부 값을 한 단계 더 풀어서 문자열로."""
    if isinstance(value, (dict, list)):
        # 한 번 더 평탄화 (중첩 깊이 2까지만)
        if isinstance(value, dict):
            return " ".join(f"{k} {v}" for k, v in value.items())
        return " ".join(str(v) for v in value)
    return str(value)


def gather_unknowns_into(
    data: Any,
    field_name: str,
    defined_fields: set[str],
) -> Any:
    """LLM이 schema 무시하고 자체 키로 보낼 때 unknown keys를 brief 필드로 흡수.

    실제 사건: 카카오 LLM이 ComposeAnbuInput에 `parent_brief` 대신 `parent_age`,
    `recent_event` 같은 자체 키로 보냄 → Pydantic이 parent_brief 누락 에러.

    동작:
    - data가 dict가 아니면 그대로 통과 (Pydantic이 처리)
    - data에 field_name 키가 이미 있고 값이 있으면 그대로 (덮어쓰지 않음)
    - 그 외엔 정의되지 않은 키들을 모아서 field_name으로 합침

    Args:
        data: model_validator(mode="before")에 들어온 raw input
        field_name: unknowns를 흡수할 대상 필드 (예: 'parent_brief')
        defined_fields: 모델에 정의된 필드 이름 집합 (cls.model_fields.keys())
    """
    if not isinstance(data, dict):
        return data
    if data.get(field_name):
        return data
    extras = {k: v for k, v in data.items() if k not in defined_fields and v is not None}
    if extras:
        data[field_name] = ", ".join(f"{k}: {v}" for k, v in extras.items())
    return data
