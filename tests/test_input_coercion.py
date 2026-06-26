"""LLM이 보낸 dict/list/None을 자동으로 str로 변환하는지 검증.

실제 사건: PlayMCP 마켓 AI 채팅에서 LLM이 'parent_brief'를 {age: 65, ...} dict로 보냄
→ Pydantic str 검증 실패 → Tool 무용지물. 이 모듈로 자동 강제 변환.
"""
from __future__ import annotations

import pytest

from servers.gift_curator.tools.curate_gifts import CurateGiftsInput
from servers.hyodo.tools.check_suspicious_message import CheckSuspiciousMessageInput
from servers.hyodo.tools.compose_anbu import ComposeAnbuInput
from shared.input_coercion import coerce_to_string


# 단위 테스트 — 헬퍼 함수

def test_coerce_string_passthrough():
    assert coerce_to_string("엄마 65세 어깨 수술") == "엄마 65세 어깨 수술"


def test_coerce_none_passthrough():
    assert coerce_to_string(None) is None


def test_coerce_dict_to_string():
    result = coerce_to_string({"age": 65, "health": "어깨 수술"})
    assert "age: 65" in result
    assert "health: 어깨 수술" in result


def test_coerce_list_to_string():
    result = coerce_to_string(["엄마", "65세", "등산"])
    assert "엄마" in result
    assert "65세" in result
    assert "등산" in result


def test_coerce_nested_dict():
    result = coerce_to_string({"profile": {"age": 65, "health": "허리"}})
    assert "profile" in result


def test_coerce_int_to_string():
    assert coerce_to_string(65) == "65"


def test_coerce_empty_dict():
    assert coerce_to_string({}) == ""


# 통합 테스트 — 실제 Tool input model에서 dict 입력 시 자동 변환

def test_compose_anbu_accepts_dict_parent_brief():
    """실제 사건 재현 — LLM이 parent_brief를 dict로 보냄."""
    inp = ComposeAnbuInput(
        parent_brief={"age": 65, "health": "어깨 수술", "interests": "등산"}
    )
    assert isinstance(inp.parent_brief, str)
    assert "age: 65" in inp.parent_brief
    assert "어깨 수술" in inp.parent_brief


def test_compose_anbu_accepts_str_parent_brief():
    """str 입력은 기존 동작 그대로."""
    inp = ComposeAnbuInput(parent_brief="엄마 65세 어깨 수술 등산 좋아함")
    assert inp.parent_brief == "엄마 65세 어깨 수술 등산 좋아함"


def test_compose_anbu_accepts_list_occasion():
    inp = ComposeAnbuInput(
        parent_brief="엄마 60대",
        occasion=["환절기", "비 오는 날"],
    )
    assert isinstance(inp.occasion, str)
    assert "환절기" in inp.occasion


def test_check_suspicious_accepts_dict_message():
    """message_text가 dict로 와도 변환."""
    inp = CheckSuspiciousMessageInput(
        message_text={"body": "긴급 대출 승인됐어요", "url": "https://fake.example"}
    )
    assert isinstance(inp.message_text, str)
    assert "긴급 대출 승인됐어요" in inp.message_text


def test_curate_gifts_accepts_dict_recipient_brief():
    """선물고민러 메인 Tool에서도 동일하게 동작."""
    inp = CurateGiftsInput(
        recipient_brief={"relationship": "친구", "age": 30, "interests": "독서"},
        budget_max=50000,
    )
    assert isinstance(inp.recipient_brief, str)
    assert "친구" in inp.recipient_brief
    assert "독서" in inp.recipient_brief


def test_compose_anbu_min_length_still_enforced():
    """coercion 후에도 min_length=1 검증은 유지."""
    with pytest.raises(ValueError):
        ComposeAnbuInput(parent_brief="")


def test_compose_anbu_empty_dict_fails_min_length():
    """빈 dict → 빈 str → min_length 검증 실패. 이게 정상."""
    with pytest.raises(ValueError):
        ComposeAnbuInput(parent_brief={})
