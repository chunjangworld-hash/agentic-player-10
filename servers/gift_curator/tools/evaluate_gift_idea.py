"""evaluate_gift_idea — 사용자가 가진 선물 후보 평가 (자문 모드).

응답 예산: <2500ms (Naver+Tavily). 캐시 적중 시 <100ms.
LLM 호출 없음 — 외부 후기 검색 + 광고 필터 + 양성 신호 점수만, 종합 판단은 호출 에이전트.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, Field, field_validator, model_validator

from shared.ad_filter import AdFilter
from shared.input_coercion import coerce_to_string, gather_unknowns_into
from shared.http_client import HttpClient
from shared.naver_search import NaverSearch
from shared.positive_signals import PositiveSignalScorer
from shared.response_builder import ResponseBuilder
from shared.tavily_search import TavilySearch

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP


class EvaluateGiftIdeaInput(BaseModel):
    gift_idea: str = Field(..., min_length=1, max_length=200)
    recipient_brief: str = Field(..., min_length=1, max_length=500)
    user_budget: int | None = Field(None, ge=1000)

    @model_validator(mode="before")
    @classmethod
    def _gather_unknowns(cls, data):
        return gather_unknowns_into(data, "gift_idea", set(cls.model_fields.keys()))

    @field_validator("gift_idea", "recipient_brief", mode="before")
    @classmethod
    def _coerce_strings(cls, v):
        return coerce_to_string(v)


async def evaluate_gift_idea(inp: EvaluateGiftIdeaInput) -> str:
    client = HttpClient()
    try:
        naver = NaverSearch(http=client)
        tavily = TavilySearch(http=client)
        ad_filter = AdFilter()
        scorer = PositiveSignalScorer()

        # gift_idea 키워드로 후기 검색
        items: list[dict] = []
        items.extend(await naver.search(inp.gift_idea, source="blog", max_results=5))
        items.extend(await tavily.search(inp.gift_idea, max_results=5))

        clean = ad_filter.filter_items(items)
        scored = scorer.assess_items(clean)

        # 카테고리별 hit 집계
        all_categories: dict[str, int] = {}
        for s in scored:
            for cat in s["_positive_score"]["categories"]:
                all_categories[cat] = all_categories.get(cat, 0) + 1
        category_summary = ", ".join(
            f"{cat}({n})" for cat, n in sorted(all_categories.items(), key=lambda x: -x[1])
        ) or "없음"

        avg_score = (
            sum(s["_positive_score"]["score"] for s in scored) / len(scored)
            if scored else 0
        )

        sections: list[tuple[str, int]] = [
            (
                f"## 💭 평가 — {inp.gift_idea}\n"
                f"받는 분: {inp.recipient_brief}",
                1,
            ),
            (
                f"### 외부 후기 시그널 (광고 제거 후)\n"
                f"- 출처 {len(clean)}곳 (원본 {len(items)}건)\n"
                f"- 평균 양성 신호 점수: {avg_score:.1f}\n"
                f"- 카테고리 분포: {category_summary}\n"
                f"- 협찬 표시: 자동 제거됨 ✅",
                1,
            ),
        ]

        if inp.user_budget:
            sections.append((
                f"### 가격 적정성\n"
                f"- 사용자 예산: {inp.user_budget:,}원\n"
                f"- 일반 가격대 비교는 호출 에이전트가 추가 검색 또는 "
                f"카카오 SearchGift로 확인 권장",
                1,
            ))

        # Top 2~3 양성 후기 발췌
        top_scored = sorted(scored, key=lambda x: x["_positive_score"]["score"], reverse=True)[:3]
        if top_scored:
            lines = ["### 대표 양성 후기 발췌"]
            for i, item in enumerate(top_scored, 1):
                url = item.get("link") or item.get("url", "")
                snippet = (item.get("description") or item.get("content", ""))[:150]
                lines.append(f"{i}. {snippet} — [{url}]({url})")
            sections.append(("\n".join(lines), 2))

        sections.append((
            "## 호출 에이전트에게\n"
            "사용자에게 이 선물 아이디어의 적합성·강점·약점을 종합 평가해주세요. "
            "필요시 refine_recommendation Tool로 대안 추천 또는 "
            "curate_gifts Tool로 새 큐레이션 제안.",
            3,
        ))

        rb = ResponseBuilder()
        return rb.build(sections, mandatory_footer="네이버 검색 기반")
    finally:
        await client.aclose()


def register(mcp: "FastMCP") -> None:
    @mcp.tool(
        name="evaluate_gift_idea",
        description=(
            "Gift Curator(선물고민러). Use this when the user already has one gift idea "
            "and wants a structured second opinion on fit, risks, and review quality. "
            "This tool explicitly calls external web search for the proposed item, "
            "filters sponsored/ad-heavy reviews with F1 rules, scores F2 "
            "genuine-satisfaction signals, and returns recipient-fit factors, price "
            "context when budget is provided, review evidence, and cautions. It does "
            "not generate a new shortlist unless the calling agent asks follow-up. "
            "LLM-free: rule-based review filtering and scoring."
        ),
        annotations={
            "title": "선물 아이디어 평가 (자문)",
            "readOnlyHint": True,
            "destructiveHint": False,
            "openWorldHint": True,
            "idempotentHint": False,
        },
    )
    async def evaluate_gift_idea_tool(inp: EvaluateGiftIdeaInput) -> str:
        return await evaluate_gift_idea(inp)
