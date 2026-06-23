"""compose_parent_warning — 부모님께 보낼 사기 경고 메시지 템플릿.

응답 예산: <30ms. 정적 템플릿 매트릭스 (사기유형 × 긴급도).
LLM 호출 없음 — 사전 큐레이션된 부모 친화 템플릿만 사용.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal

from pydantic import BaseModel, Field

from shared.response_builder import ResponseBuilder

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

_TEMPLATES_PATH = (
    Path(__file__).resolve().parent.parent / "data" / "parent_warning_templates.json"
)


# 사용자 입력(자유 텍스트)을 templates의 scam_type_id로 매핑하기 위한 키워드 사전.
# scam_patterns.json의 8개 유형(Top 8)에 대응. 부분 매칭 (in 연산자).
_SCAM_TYPE_KEYWORDS: dict[str, tuple[str, ...]] = {
    "loan": ("대출", "대환", "저금리", "승인"),
    "delivery": ("택배", "배송", "운송", "물류"),
    "government_admin": ("정부", "공공", "과태료", "범칙금", "벌점", "행정"),
    "law_enforcement": ("검찰", "경찰", "금감원", "수사", "보이스피싱"),
    "card_payment": ("카드", "해외결제", "미승인", "결제"),
    "family_impersonation": ("가족", "자녀", "딸", "아들", "지인", "메신저피싱"),
    "government_support": ("지원금", "쿠폰", "소비쿠폰", "재난"),
    "resident_center": ("주민센터", "등본", "발급"),
}


class ComposeParentWarningInput(BaseModel):
    scam_type: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="감지된 사기 유형(자유 텍스트). 예: '대출 사기', '택배 사칭'.",
    )
    parent_brief: str | None = Field(
        None,
        max_length=500,
        description="부모님 연령·관계 등 호출 에이전트의 추가 컨텍스트.",
    )
    urgency: Literal["low", "medium", "high"] = Field(
        "medium",
        description="긴급도. low는 medium 톤으로 폴백.",
    )


@lru_cache(maxsize=1)
def _load_templates() -> dict[str, Any]:
    with open(_TEMPLATES_PATH, encoding="utf-8") as fp:
        return json.load(fp)


def _resolve_scam_type_id(scam_type: str) -> str | None:
    """사용자 입력에서 가장 일치도 높은 scam_type_id를 추출. 없으면 None."""
    text = scam_type.lower()
    # 가장 많은 키워드가 매칭되는 유형을 채택
    best_id: str | None = None
    best_hits = 0
    for scam_id, keywords in _SCAM_TYPE_KEYWORDS.items():
        hits = sum(1 for kw in keywords if kw in text)
        if hits > best_hits:
            best_hits = hits
            best_id = scam_id
    return best_id


def _pick_template(
    templates: list[dict[str, Any]],
    scam_type_id: str | None,
    urgency: str,
) -> dict[str, Any] | None:
    """scam_type_id + urgency 우선, 동일 유형 다른 urgency 폴백."""
    # low는 medium 풀로 폴백
    effective_urgency = "medium" if urgency == "low" else urgency

    if scam_type_id is None:
        return None

    same_type = [t for t in templates if t["scam_type_id"] == scam_type_id]
    if not same_type:
        return None

    exact = [t for t in same_type if t["urgency"] == effective_urgency]
    if exact:
        return exact[0]
    return same_type[0]


def compose_parent_warning(inp: ComposeParentWarningInput) -> str:
    data = _load_templates()
    templates: list[dict[str, Any]] = data["templates"]
    universal_tips: list[str] = data["universal_safety_tips"]
    contacts: list[dict[str, Any]] = data["universal_emergency_contacts"]

    scam_type_id = _resolve_scam_type_id(inp.scam_type)
    tpl = _pick_template(templates, scam_type_id, inp.urgency)

    sections: list[tuple[str, int]] = [
        ("## 부모님께 보낼 경고 메시지 템플릿", 1),
    ]

    if tpl is not None:
        # 매칭된 템플릿 사용
        sections.append(
            (
                f"### 감지된 사기 유형: {tpl['scam_type_name']} "
                f"(긴급도: {inp.urgency})",
                1,
            )
        )
        sections.append((f"**부모님 친화 경고 메시지**\n\n{tpl['warning_message']}", 1))

        action_block = "**부모님이 해야 할 행동**\n" + "\n".join(
            f"{i}. {step}" for i, step in enumerate(tpl["action_steps"], 1)
        )
        sections.append((action_block, 1))

        sections.append((f"**핵심 안전 수칙**\n- {tpl['safety_tip']}", 2))
    else:
        # 폴백: Top 8 외 유형 — 사용자 입력값 + 범용 메시지
        fallback_warning = (
            f"🚨 엄마/아빠, '{inp.scam_type}' 관련 의심 메시지를 받으셨다면 "
            "**절대 링크를 누르지 마시고** 자녀에게 먼저 연락해 주세요.\n\n"
            "사기 유형이 새롭더라도 원칙은 같아요: "
            "**의심·확인·신고**. 익숙하지 않은 요청은 무조건 자녀에게 확인."
        )
        sections.append(
            (
                f"### 감지된 사기 유형: {inp.scam_type} "
                f"(긴급도: {inp.urgency}, 매칭 템플릿 없음 — 범용 가이드)",
                1,
            )
        )
        sections.append((f"**부모님 친화 경고 메시지**\n\n{fallback_warning}", 1))
        sections.append(
            (
                "**부모님이 해야 할 행동**\n"
                "1. 메시지 안의 링크/번호 절대 누르지 마세요\n"
                "2. 자녀에게 메시지 캡처 전송\n"
                "3. 의심되면 118(KISA)로 신고",
                1,
            )
        )

    # 범용 안전 수칙
    sections.append(
        (
            "### 알아두실 안전 수칙 (모든 사기 공통)\n"
            + "\n".join(f"- {tip}" for tip in universal_tips),
            2,
        )
    )

    # 비상 연락처 (high urgency에서는 우선순위 ↑)
    contact_priority = 1 if inp.urgency == "high" else 2
    contact_lines = []
    for c in contacts:
        if "number" in c:
            contact_lines.append(
                f"- **{c['name']}**: {c['number']} ({c.get('available', '')})"
            )
        else:
            contact_lines.append(
                f"- **{c['name']}**: {c.get('channel', '')} — {c.get('purpose', '')}"
            )
    sections.append(
        (
            "### 신고·구제 연락처\n" + "\n".join(contact_lines),
            contact_priority,
        )
    )

    # 호출 에이전트 가이드
    parent_context = (
        f"\n\n부모님 컨텍스트: {inp.parent_brief}" if inp.parent_brief else ""
    )
    sections.append(
        (
            "## 호출 에이전트에게\n"
            "위 템플릿을 부모님 친화 어조로 다듬어 자녀에게 보여주세요. "
            "긴 설명보다 짧고 분명한 표현 우선. 사기 유형별 핵심 한 줄 강조. "
            "부모님 연령·관계가 주어졌다면 호칭과 어휘를 그에 맞게 조정해 주세요."
            + parent_context,
            3,
        )
    )

    rb = ResponseBuilder()
    return rb.build(sections)


def register(mcp: "FastMCP") -> None:
    """FastMCP Tool 등록."""

    @mcp.tool(
        name="compose_parent_warning",
        description=(
            "Hyodo Secretary(효도비서). Generate a parent-friendly warning message "
            "template about a detected scam, suitable for the user to forward to their "
            "parent. Returns structured templates (warning in elderly-friendly Korean, "
            "step-by-step action guide, suggested follow-up channels) tailored to the "
            "parent's age/profile. Does not call LLM internally - uses pre-curated "
            "elderly-friendly templates. Use this after check_suspicious_message returns "
            "a high-risk verdict and the user wants help warning their parent."
        ),
        annotations={
            "title": "부모님께 보낼 경고 메시지",
            "readOnlyHint": True,
            "destructiveHint": False,
            "openWorldHint": False,
            "idempotentHint": True,
        },
    )
    def compose_parent_warning_tool(inp: ComposeParentWarningInput) -> str:
        return compose_parent_warning(inp)
