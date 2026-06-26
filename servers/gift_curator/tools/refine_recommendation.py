"""refine_recommendation — 사용자 피드백 반영 재추천. curate_gifts 위 얇은 래퍼.

응답 예산: curate_gifts와 동일 (<2500ms).
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from servers.gift_curator.tools.curate_gifts import CurateGiftsInput, curate_gifts
from shared.input_coercion import coerce_to_string, gather_unknowns_into

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP


_DIRECTION_LABELS = {
    "cheaper": "더 저렴하게",
    "more_expensive": "더 고급으로",
    "different_category": "다른 카테고리로",
    "more_practical": "더 실용적으로",
    "more_emotional": "더 감성적으로",
    "more_special": "더 특별하게",
    "less_serious": "덜 격식 차리게",
    "more_serious": "더 격식 있게",
    "smaller": "더 작은 규모로",
    "bigger": "더 큰 규모로",
}


class RefineRecommendationInput(BaseModel):
    previous_keywords: list[str] = Field(..., max_length=10)
    feedback_direction: Literal[
        "cheaper", "more_expensive", "different_category",
        "more_practical", "more_emotional", "more_special",
        "less_serious", "more_serious", "smaller", "bigger",
    ]
    recipient_brief: str = Field(..., min_length=1, max_length=500)
    new_budget_max: int | None = Field(None, ge=1000)

    @model_validator(mode="before")
    @classmethod
    def _gather_unknowns(cls, data):
        return gather_unknowns_into(data, "recipient_brief", set(cls.model_fields.keys()))

    @field_validator("recipient_brief", mode="before")
    @classmethod
    def _coerce_strings(cls, v):
        return coerce_to_string(v)


async def refine_recommendation(inp: RefineRecommendationInput) -> str:
    refined = CurateGiftsInput(
        recipient_brief=inp.recipient_brief,
        budget_max=inp.new_budget_max,
        avoid_categories=inp.previous_keywords,
    )
    base_result = await curate_gifts(refined)

    label = _DIRECTION_LABELS.get(inp.feedback_direction, inp.feedback_direction)
    prefix = (
        f"## 🔁 재추천 (방향: {label} / `{inp.feedback_direction}`)\n"
        f"이전 추천 회피: {', '.join(inp.previous_keywords)}\n\n"
    )
    return prefix + base_result


def register(mcp: "FastMCP") -> None:
    @mcp.tool(
        name="refine_recommendation",
        description=(
            "Gift Curator(선물고민러). Use this only after curate_gifts or "
            "evaluate_gift_idea when the user gives directional feedback such as too "
            "expensive, wrong style, already bought, avoid category, more practical, "
            "or more premium. The calling agent should convert free-form feedback into "
            "structured feedback_direction and previous_keywords. This tool explicitly "
            "calls external web search again, avoids prior keywords, reapplies F1 ad "
            "filters and F2 satisfaction scoring, and returns 3 revised candidates in "
            "the same Gift MCP compatible format. LLM-free: rule-based re-ranking and "
            "exclusion logic."
        ),
        annotations={
            "title": "선물 재추천 (피드백 반영)",
            "readOnlyHint": True,
            "destructiveHint": False,
            "openWorldHint": True,
            "idempotentHint": False,
        },
    )
    async def refine_recommendation_tool(inp: RefineRecommendationInput) -> str:
        return await refine_recommendation(inp)
