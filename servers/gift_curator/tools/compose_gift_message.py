"""compose_gift_message — 선물 카드 메시지 템플릿 생성.

응답 예산: <30ms. 정적 템플릿 + 관계×행사 매트릭스.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING, Literal

from pydantic import BaseModel, Field, field_validator

from shared.input_coercion import coerce_to_string
from shared.response_builder import ResponseBuilder

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

_DATA_DIR = Path(__file__).resolve().parent.parent / "data"
_TEMPLATES_PATH = _DATA_DIR / "message_templates.json"
_TONE_MAP_PATH = _DATA_DIR / "relationship_tone_map.json"


class ComposeGiftMessageInput(BaseModel):
    gift_name: str = Field(..., min_length=1, max_length=100)
    recipient_relationship: Literal[
        "parent", "sibling", "friend", "colleague",
        "boss", "client", "lover", "in_law", "child", "other"
    ]
    occasion: str = Field(..., min_length=1, max_length=100)
    tone_preference: Literal["formal", "casual", "heartfelt"] | None = None

    @field_validator("gift_name", "occasion", mode="before")
    @classmethod
    def _coerce_strings(cls, v):
        return coerce_to_string(v)


@lru_cache(maxsize=1)
def _load_templates() -> list[dict]:
    with open(_TEMPLATES_PATH, encoding="utf-8") as fp:
        data = json.load(fp)
    return data.get("templates", [])


@lru_cache(maxsize=1)
def _load_tone_map() -> dict[str, dict]:
    with open(_TONE_MAP_PATH, encoding="utf-8") as fp:
        data = json.load(fp)
    # Build id-indexed dict from relationships list
    return {r["id"]: r for r in data.get("relationships", [])}


_TONE_LABELS = {"formal": "정중 톤", "heartfelt": "따뜻한 톤", "casual": "캐주얼 톤"}


def _collect_by_tone(templates: list[dict], relationship: str, occasion: str) -> dict[str, list[str]]:
    """동일 relationship + 부분 일치 occasion 으로 톤별 메시지 수집."""
    by_tone: dict[str, list[str]] = {"formal": [], "heartfelt": [], "casual": []}
    for t in templates:
        if t.get("relationship") != relationship:
            continue
        # occasion 부분 일치 (괄호 안 부가어 등을 허용)
        t_occ = t.get("occasion", "")
        if occasion in t_occ or t_occ in occasion:
            tone = t.get("tone")
            if tone in by_tone:
                msg = t.get("main_message", "")
                short = t.get("short_variation", "")
                if msg:
                    by_tone[tone].append(msg)
                if short and short != msg:
                    by_tone[tone].append(short)
    return by_tone


def _fallback_messages(relationship: str, occasion: str, tone_map: dict[str, dict]) -> dict[str, list[str]]:
    """매칭 실패 시 generic 톤별 메시지 생성. occasion 변수 포함."""
    rel_info = tone_map.get(relationship, {})
    rel_name = rel_info.get("name", relationship)
    return {
        "formal": [
            f"{rel_name}께 {occasion}을(를) 진심으로 축하드립니다. 늘 건강하시길 바랍니다.",
        ],
        "heartfelt": [
            f"{occasion} 정말 축하해요. 마음 가득 담아 전해요.",
            f"{rel_name}에게 {occasion}의 따뜻한 마음을 전합니다.",
        ],
        "casual": [
            f"{occasion} 축하 🎉 즐거운 시간 보내요!",
        ],
    }


def compose_gift_message(inp: ComposeGiftMessageInput) -> str:
    templates = _load_templates()
    tone_map = _load_tone_map()

    by_tone = _collect_by_tone(templates, inp.recipient_relationship, inp.occasion)
    fallback = _fallback_messages(inp.recipient_relationship, inp.occasion, tone_map)
    # 비어있는 톤은 fallback으로 채워서 사용자가 톤 비교를 할 수 있게 보장
    for tone_key in by_tone:
        if not by_tone[tone_key]:
            by_tone[tone_key] = fallback.get(tone_key, [])

    rel_info = tone_map.get(inp.recipient_relationship, {})
    recommended_tone = rel_info.get("default_tone", "heartfelt")
    rel_name_kor = rel_info.get("name", inp.recipient_relationship)

    sections: list[tuple[str, int]] = [
        (
            f"## 💌 메시지 카드 초안 — {rel_name_kor} {inp.occasion} ({inp.gift_name})",
            1,
        ),
    ]

    for tone_key, label in _TONE_LABELS.items():
        if inp.tone_preference and inp.tone_preference != tone_key:
            continue
        messages = by_tone.get(tone_key, [])
        if not messages:
            continue
        recommended_mark = (
            " ⭐ (이 관계에 추천)"
            if tone_key == recommended_tone and not inp.tone_preference
            else ""
        )
        lines = [f"### {label}{recommended_mark}"]
        for msg in messages[:3]:
            lines.append(f'"{msg}"')
        sections.append(("\n".join(lines), 2))

    if not inp.tone_preference:
        sections.append(
            (
                "## 호출 에이전트에게\n"
                "사용자가 톤 선호를 명시했다면 그 톤만 보여주고, "
                "안 했다면 추천 톤(⭐)을 강조해 제시해주세요. "
                f"선물({inp.gift_name})의 특성과 메시지가 자연스럽게 연결되도록 한 줄 덧붙여도 좋습니다.",
                3,
            )
        )

    rb = ResponseBuilder()
    return rb.build(sections)


def register(mcp: "FastMCP") -> None:
    """FastMCP Tool 등록."""

    @mcp.tool(
        name="compose_gift_message",
        description=(
            "Gift Curator(선물고민러). Use this when the user has already chosen or "
            "nearly chosen a gift and needs a short Korean message card, enclosure "
            "note, or chat-ready line for the recipient. Returns 2-3 template variants "
            "by relationship, occasion, formality, and emotional intensity, plus a "
            "tone-selection guide. It does not recommend products or search reviews; "
            "call curate_gifts or evaluate_gift_idea first when the item is not "
            "settled. LLM-free: curated Korean gift-message templates with rule-based "
            "slot filling."
        ),
        annotations={
            "title": "선물 메시지 카드 초안",
            "readOnlyHint": True,
            "destructiveHint": False,
            "openWorldHint": False,
            "idempotentHint": True,
        },
    )
    def compose_gift_message_tool(inp: ComposeGiftMessageInput) -> str:
        return compose_gift_message(inp)
