"""compose_anbu — 부모님 안부 메시지 컨텍스트 데이터 생성.

응답 예산: <50ms. 정적 시즌 데이터 + parent_brief 파싱.
실제 메시지 생성은 호출 에이전트(LLM)가 담당.
"""
from __future__ import annotations

import json
from datetime import date
from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from shared.input_coercion import coerce_to_string, gather_unknowns_into
from shared.response_builder import ResponseBuilder

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

_DATA_DIR = Path(__file__).resolve().parent.parent / "data"


class ComposeAnbuInput(BaseModel):
    parent_brief: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="부모님 관계·연령·건강·관심사를 자유 텍스트로. 예: '엄마 60대 허리 안 좋음 등산 시작'.",
    )
    occasion: str | None = Field(
        None,
        max_length=200,
        description="특별한 상황. 예: '비 오는 날', '환절기', '명절 전날'.",
    )
    tone: Literal["warm_polite", "brief", "playful"] = Field(
        "warm_polite",
        description="안부 메시지 어조. warm_polite(따뜻·정중) / brief(간결) / playful(장난).",
    )
    image_base64: str | None = Field(
        None,
        description="Forward compat. 카카오톡 이미지 입력 지원 시 사용. 현재 미사용.",
    )

    @model_validator(mode="before")
    @classmethod
    def _gather_unknowns(cls, data):
        return gather_unknowns_into(data, "parent_brief", set(cls.model_fields.keys()))

    @field_validator("parent_brief", "occasion", "image_base64", mode="before")
    @classmethod
    def _coerce_strings(cls, v):
        return coerce_to_string(v)


@lru_cache(maxsize=1)
def _load_seasonal_keywords() -> dict[str, Any]:
    with open(_DATA_DIR / "seasonal_keywords.json", encoding="utf-8") as fp:
        return json.load(fp)


@lru_cache(maxsize=1)
def _load_health_risks() -> dict[str, Any]:
    with open(_DATA_DIR / "health_seasonal_risks.json", encoding="utf-8") as fp:
        return json.load(fp)


@lru_cache(maxsize=1)
def _load_trending() -> dict[str, Any]:
    with open(_DATA_DIR / "trending_topic_categories.json", encoding="utf-8") as fp:
        return json.load(fp)


@lru_cache(maxsize=1)
def _load_tone_templates() -> dict[str, Any]:
    with open(_DATA_DIR / "tone_templates.json", encoding="utf-8") as fp:
        return json.load(fp)


_RELATION_KWS = (
    "엄마", "아빠", "어머니", "아버지",
    "할머니", "할아버지",
    "장모", "장인", "시어머니", "시아버지",
)
_AGE_KWS = ("50대", "60대", "70대", "80대", "90대")
_HEALTH_KWS = ("허리", "무릎", "혈압", "당뇨", "관절", "치매", "위", "심장", "어깨", "눈", "치아")
_INTEREST_KWS = ("등산", "여행", "독서", "골프", "텃밭", "낚시", "요리", "그림", "산책", "사진", "음악")


def _extract_parent_profile(brief: str) -> dict[str, str | None]:
    """parent_brief에서 관계·연령·건강·관심사 추출 (단순 키워드 매칭).

    ⚠️ 단순 substring 매칭 — "장모님"(님 suffix)은 "장모" prefix로 잡힘.
       호칭 변형 정밀 매칭은 Phase 2.2 후속에서 보강.
    """
    relation = next((r for r in _RELATION_KWS if r in brief), None)
    age = next((a for a in _AGE_KWS if a in brief), None)
    health_hits = [kw for kw in _HEALTH_KWS if kw in brief]
    interest_hits = [kw for kw in _INTEREST_KWS if kw in brief]

    return {
        "relation": relation,
        "age_decade": age,
        "health": ", ".join(health_hits) if health_hits else None,
        "interests": ", ".join(interest_hits) if interest_hits else None,
    }


def _current_season_context(today: date | None = None) -> dict[str, Any]:
    """월 기반 시즌 키워드 + 건강 주의 + 절기."""
    today = today or date.today()
    month = today.month
    seasonal = _load_seasonal_keywords()
    health_risks = _load_health_risks()

    # seasonal_keywords.json: top-level "months" is a list of {month, name, keywords, seasonal_events}
    months_list = seasonal.get("months", [])
    month_entry: dict[str, Any] = next(
        (m for m in months_list if m.get("month") == month), {}
    )
    season_keywords = month_entry.get("keywords", []) or []
    seasonal_events = month_entry.get("seasonal_events", []) or []

    # health_seasonal_risks.json: by_month dict keyed by month string
    health_month: dict[str, Any] = health_risks.get("by_month", {}).get(str(month), {})

    return {
        "current_month": month,
        "season_keywords": season_keywords,
        "seasonal_events": seasonal_events,
        "check_in_topics": health_month.get("check_in_topics", []),
        "health_risks": health_month.get("risks", []),
    }


def _filter_trending_categories(
    trending: dict[str, Any],
) -> list[dict[str, Any]]:
    """트렌드 화제 카테고리 상위 N개 반환.

    현재는 단순 slice — Phase 2.2 후속에서 건강 회피 로직 추가 가능.
    """
    cats = trending.get("categories", []) or []
    # cats: list of {id, name, description, sample_topics_2026, tone_guidance, when_to_use}
    return cats[:6]


def compose_anbu(inp: ComposeAnbuInput) -> str:
    profile = _extract_parent_profile(inp.parent_brief)
    season = _current_season_context()
    trending = _load_trending()
    tone_templates = _load_tone_templates()

    sections: list[tuple[str, int]] = []

    # 1. 부모님 프로필
    sections.append(
        (
            "## 부모님 프로필 (추출됨)\n"
            f"- 관계: {profile['relation'] or '미상'}\n"
            f"- 연령대: {profile['age_decade'] or '미상'}\n"
            f"- 건강 이슈: {profile['health'] or '없음'}\n"
            f"- 관심사: {profile['interests'] or '없음'}\n"
            f"- 원문: {inp.parent_brief}",
            1,
        )
    )

    # 2. 시즌 컨텍스트
    season_events_str = (
        ", ".join(
            f"{ev.get('name', '')}({ev.get('date_pattern', '')})"
            for ev in season["seasonal_events"][:5]
        )
        or "없음"
    )
    sections.append(
        (
            f"## 시즌 컨텍스트 (현재 {season['current_month']}월)\n"
            f"- 안부 키워드: {', '.join(season['season_keywords']) or '없음'}\n"
            f"- 이달의 절기·이벤트: {season_events_str}\n"
            f"- 챙길 화제: {', '.join(season['check_in_topics']) or '없음'}\n"
            f"- 건강 주의: {', '.join(season['health_risks']) or '없음'}",
            1,
        )
    )

    # 3. occasion
    if inp.occasion:
        sections.append((f"## 특별 occasion\n{inp.occasion}", 1))

    # 4. 트렌드 화제 카테고리
    trend_cats = _filter_trending_categories(trending)
    trend_lines = []
    for cat in trend_cats:
        name = cat.get("name", cat.get("id", ""))
        desc = cat.get("description", "")
        tone_guide = cat.get("tone_guidance", "")
        trend_lines.append(f"- **{name}** — {desc}\n  · 톤 가이드: {tone_guide}")
    sections.append(
        (
            "## 트렌드 화제 후보 (호출 에이전트가 시점별 구체화)\n"
            + "\n".join(trend_lines),
            2,
        )
    )

    # 5. 톤 템플릿 (선택된 tone만 노출)
    selected_tone_examples = tone_templates.get(inp.tone, [])
    if isinstance(selected_tone_examples, list):
        tpl_lines = []
        for ex in selected_tone_examples[:8]:
            if isinstance(ex, dict):
                tpl = ex.get("template", "")
                ctx = ex.get("context", "")
                tpl_lines.append(f"- `{tpl}` (context: {ctx})")
        tone_block = (
            f"## 추천 톤: {inp.tone}\n"
            f"### 템플릿 예시 (자리표시자 치환은 호출 에이전트가 수행)\n"
            + ("\n".join(tpl_lines) if tpl_lines else "- (템플릿 없음)")
        )
    else:
        tone_block = f"## 추천 톤: {inp.tone}"
    sections.append((tone_block, 2))

    # 6. 호출 에이전트 fancy 톤 가이드 (Phase 2.6 — UX 흐름 강화)
    tone_label = {
        "warm_polite": "따스함",
        "brief": "간결",
        "playful": "가벼움/장난",
    }.get(inp.tone, inp.tone)
    sections.append(
        (
            "## ✏️ 호출 에이전트 작성 지침\n"
            "**fancy 톤 원칙 — 반드시 준수**\n"
            "1. 사용자가 알려준 호칭을 parent_brief에서 그대로 사용 (엄마/어머니/엄니/아빠/아부지 등). "
            "LLM이 임의로 변경 ❌\n"
            "2. 길이 1-2문장. 잔소리·훈계·교과서 톤 ❌. '~으세요' 남발 ❌\n"
            "3. 끝에 '이 메시지는 ...입니다' 같은 메타 해설 절대 금지\n"
            "4. 이모지 0-1개. 정말 어울릴 때만 (남발 ❌)\n"
            "5. 가족 톡방에서 실제로 쓸 만한 자연스러운 한국어\n\n"
            "**트렌드 한 톨 녹이기 (일반 LLM과 차별점)**\n"
            "6. 위 시즌 키워드 + 이달의 절기·이벤트 + 트렌드 카테고리 중 1-2개를 자연스럽게 결합\n"
            "7. 본인의 한국 시사·뉴스·계절 트렌드 지식을 한 톨 보태기\n"
            f"8. 사용자가 고른 톤 = `{inp.tone}` ({tone_label}). occasion이 있다면 우선 반영\n\n"
            "**안전 가드**\n"
            "9. 부모님 건강 이슈가 위 프로필에 있다면 그 카테고리는 회피 또는 가볍게 다루기\n"
            "10. 정치 화제는 선거 시기 외엔 회피. 정확한 수치(주가·시청률 등) 단정 ❌ → '~다는데' 톤\n\n"
            "**메시지 작성 후 — 사용자에게 옵션 카드 제시**\n"
            "'이대로 보내실래요? 아니면:\n"
            " 🔄 다른 결로 다시 (더 가볍게 / 더 따스하게 / 시즌감 추가)\n"
            " 🎯 다른 주제로 다시 (건강 / 일상 / 취미 / 요즘 화제 / 옛 추억)\n"
            " 💾 나챗방에 저장 (save_to_memo_chat Tool 호출)'\n\n"
            "**예시 결 (참고)**\n"
            "- 따스하게: '엄마 장마라 무릎 시큰거리진 않아요? 등산은 비 그치고 가요'\n"
            "- 가볍게: '아빠 요즘 트로트 가왕 누구 본대요? 다음에 통화하면 알려줘봐요'\n"
            "- 슬쩍: '엄마 보고싶다 🤍'\n"
            "- 시즌감: '아부지, 망종 지나니까 비 잦네요. 골프장은 잠시 쉬세요'",
            3,
        )
    )

    rb = ResponseBuilder()
    return rb.build(sections)


def register(mcp: "FastMCP") -> None:
    """FastMCP Tool 등록."""

    @mcp.tool(
        name="compose_anbu",
        description=(
            "Hyodo Secretary(효도비서). Use this when the user wants help preparing a "
            "daily, weekly, seasonal, or event-linked greeting message for an elderly "
            "parent. Returns structured greeting context: relationship cues, "
            "recent-event framing, seasonal keywords, respect level, tone guidance, "
            "and 2-3 Korean template fragments for the calling agent to assemble. It "
            "is not a generic chat writer or web-search wrapper. LLM-free: uses "
            "curated Korean parent-message templates, calendar cues, and simple "
            "profile fields."
        ),
        annotations={
            "title": "안부 한 줄 만들기",
            "readOnlyHint": True,
            "destructiveHint": False,
            "openWorldHint": False,
            "idempotentHint": False,  # 날짜 따라 시즌 다름
        },
    )
    def compose_anbu_tool(inp: ComposeAnbuInput) -> str:
        return compose_anbu(inp)
