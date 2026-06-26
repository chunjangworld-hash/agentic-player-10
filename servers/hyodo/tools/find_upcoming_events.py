"""find_upcoming_events — 시즌 + 개인 이벤트 캘린더 검색.

응답 예산: <50ms. 정적 캘린더 + 날짜 계산 + parent_brief 파싱.
실제 우선순위 정리는 호출 에이전트(LLM)가 담당.
"""
from __future__ import annotations

import json
import re
from datetime import date
from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field, field_validator, model_validator

from shared.input_coercion import coerce_to_string, gather_unknowns_into
from shared.response_builder import ResponseBuilder

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

_EVENTS_PATH = Path(__file__).resolve().parent.parent / "data" / "seasonal_events.json"

_MILESTONE_KWS = (
    ("환갑", "환갑"),
    ("칠순", "칠순"),
    ("팔순", "팔순"),
    ("생신", "생신"),
    ("결혼기념일", "결혼기념일"),
)


class FindUpcomingEventsInput(BaseModel):
    parent_brief: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="부모님 관계·연령·기념일 등. 예: '엄마 60대 생신 8월 15일'.",
    )
    upcoming_days: int = Field(
        60,
        ge=7,
        le=365,
        description="앞으로 며칠 범위에서 이벤트를 검색할지. 7~365.",
    )

    @model_validator(mode="before")
    @classmethod
    def _gather_unknowns(cls, data):
        return gather_unknowns_into(data, "parent_brief", set(cls.model_fields.keys()))

    @field_validator("parent_brief", mode="before")
    @classmethod
    def _coerce_strings(cls, v):
        return coerce_to_string(v)


@lru_cache(maxsize=1)
def _load_events() -> dict:
    with open(_EVENTS_PATH, encoding="utf-8") as fp:
        return json.load(fp)


def _extract_personal_dates(brief: str) -> list[dict]:
    """parent_brief에서 '8월 15일', '12/3', '환갑' 같은 개인 날짜·마일스톤 추출."""
    personal: list[dict] = []
    for m in re.finditer(r"(\d{1,2})월\s*(\d{1,2})일", brief):
        personal.append({
            "name": "개인 이벤트",
            "month": int(m.group(1)),
            "day": int(m.group(2)),
            "kind": "월일",
        })
    for m in re.finditer(r"(\d{1,2})/(\d{1,2})", brief):
        personal.append({
            "name": "개인 이벤트",
            "month": int(m.group(1)),
            "day": int(m.group(2)),
            "kind": "슬래시",
        })
    for kw, label in _MILESTONE_KWS:
        if kw in brief:
            personal.append({"name": label, "kind": "마일스톤"})
    return personal


def _days_until(target_month: int, target_day: int, today: date) -> int:
    try:
        this_year = today.replace(month=target_month, day=target_day)
    except ValueError:
        return -1  # 잘못된 날짜 (예: 2/30)
    if this_year < today:
        try:
            next_year = today.replace(
                year=today.year + 1, month=target_month, day=target_day
            )
            return (next_year - today).days
        except ValueError:
            return -1
    return (this_year - today).days


def find_upcoming_events(
    inp: FindUpcomingEventsInput, today: date | None = None
) -> str:
    today = today or date.today()
    events_data = _load_events()

    upcoming: list[dict] = []

    # Solar events (절기, 공휴일, 기념일)
    for ev in events_data.get("solar_events", []):
        date_str = ev.get("date_approx", "")
        try:
            month, day = map(int, date_str.split("-"))
        except (ValueError, AttributeError):
            continue
        days = _days_until(month, day, today)
        if 0 <= days <= inp.upcoming_days:
            upcoming.append({
                "name": ev.get("name", ev.get("id", "이벤트")),
                "days": days,
                "category": ev.get("category", "절기"),
            })

    # Personal events (월일이 있는 경우만 D-X 계산)
    for p in _extract_personal_dates(inp.parent_brief):
        if "month" in p:
            days = _days_until(p["month"], p["day"], today)
            if 0 <= days <= inp.upcoming_days:
                upcoming.append({
                    "name": p["name"],
                    "days": days,
                    "category": "개인 기념일",
                })

    # Mark milestone keywords without dates as "기념해야 할 사항 (날짜 미상)"
    milestone_only = [
        p["name"]
        for p in _extract_personal_dates(inp.parent_brief)
        if "month" not in p
    ]

    upcoming.sort(key=lambda x: x["days"])

    sections: list[tuple[str, int]] = [
        (f"## 다가오는 챙길 일 (앞으로 {inp.upcoming_days}일)", 1)
    ]

    for ev in upcoming[:15]:
        sections.append((
            f"### D-{ev['days']} — {ev['name']} ({ev['category']})",
            1,
        ))

    if milestone_only:
        sections.append((
            "## 알려진 마일스톤 (날짜 미상 — 정확한 날짜 알려주시면 카운트다운 가능)\n"
            + "\n".join(f"- {m}" for m in milestone_only),
            2,
        ))

    if not upcoming and not milestone_only:
        sections.append((
            "_해당 기간에 등록된 이벤트가 없어요. 일상 안부로 챙기시는 게 좋겠어요._",
            2,
        ))

    sections.append((
        "## 호출 에이전트에게\n"
        "위 이벤트들을 보고 자녀에게 '지금부터 챙기면 좋을 일'을 "
        "우선순위 순으로 정리해주세요. 선물 추천이 필요하면 사용자에게 "
        "선물고민러 도구 사용을 안내해주세요.",
        3,
    ))

    rb = ResponseBuilder()
    return rb.build(sections)


def register(mcp: "FastMCP") -> None:
    """FastMCP Tool 등록."""

    @mcp.tool(
        name="find_upcoming_events",
        description=(
            "Hyodo Secretary(효도비서). Use this when the user asks what parent-related "
            "dates, seasonal issues, or upcoming check-in opportunities should be "
            "considered before composing a message or reminder. Returns a structured "
            "event list from static Korean calendar data plus simple extraction from "
            "parent_brief, including date window, event type, relevance reason, and "
            "suggested check-in action. It does not create the final greeting; call "
            "compose_anbu next if the user wants message wording. LLM-free: "
            "deterministic calendar lookup and pattern extraction."
        ),
        annotations={
            "title": "부모님 챙길 일 찾기",
            "readOnlyHint": True,
            "destructiveHint": False,
            "openWorldHint": False,
            "idempotentHint": False,
        },
    )
    def find_upcoming_events_tool(inp: FindUpcomingEventsInput) -> str:
        return find_upcoming_events(inp)
