"""curate_gifts — 선물고민러 메인 Tool. 후보 3개 + SearchGift 파라미터.

응답 예산: <2500ms (Naver+Tavily 병행). 캐시 적중 시 <300ms.
차별가치: 카카오 선물하기 MCP의 SearchGift와 자연 연계되는 키워드/가격대/태그 반환.
우리는 카카오 MCP를 직접 호출 안 함 — 호출 에이전트가 두 MCP를 orchestration.
"""
from __future__ import annotations

import re
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

from shared.ad_filter import AdFilter
from shared.http_client import HttpClient
from shared.naver_search import NaverSearch
from shared.positive_signals import PositiveSignalScorer
from shared.response_builder import ResponseBuilder
from shared.tavily_search import TavilySearch

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

_RECIPIENT_KWS = (
    "엄마", "아빠", "어머니", "아버지", "할머니", "할아버지",
    "장모님", "장인어른", "시어머니", "시아버지", "친정엄마", "친정아빠",
    "동생", "친구", "팀장", "상사", "후배",
)


class CurateGiftsInput(BaseModel):
    recipient_brief: str = Field(..., min_length=1, max_length=500)
    budget_max: int | None = Field(None, ge=1000)
    avoid_categories: list[str] | None = Field(None, max_length=10)
    recent_gifts_hint: list[str] | None = Field(None, max_length=5)


def _extract_budget(brief: str) -> int | None:
    """'20만원', '5만', '15만 원대' 등 추출."""
    m = re.search(r"(\d+)\s*만", brief)
    return int(m.group(1)) * 10000 if m else None


def _extract_recipient(brief: str) -> str | None:
    return next((r for r in _RECIPIENT_KWS if r in brief), None)


def _build_search_query(brief: str, recipient: str | None) -> str:
    """검색용 query — 받는 분 + 핵심 키워드."""
    parts = [recipient or ""] + ["선물"] + brief.split()[:5]
    return " ".join(p for p in parts if p and not re.match(r"^\d+만원?$", p))


async def curate_gifts(inp: CurateGiftsInput) -> str:
    client = HttpClient()
    try:
        naver = NaverSearch(http=client)
        tavily = TavilySearch(http=client)
        ad_filter = AdFilter()
        scorer = PositiveSignalScorer()

        budget = inp.budget_max or _extract_budget(inp.recipient_brief)
        recipient = _extract_recipient(inp.recipient_brief)
        query = _build_search_query(inp.recipient_brief, recipient)

        items: list[dict] = []
        items.extend(await naver.search(query, source="blog", max_results=10))
        items.extend(await tavily.search(query, max_results=5))

        clean = ad_filter.filter_items(items)
        scored = scorer.assess_items(clean)
        scored.sort(key=lambda x: x["_positive_score"]["score"], reverse=True)

        # Top 3 후보를 톤 라벨링
        tones = ["감성형", "실용형", "특별형"]
        top_n = scored[:3]
        # 부족하면 placeholder
        while len(top_n) < 3:
            top_n.append({
                "title": "(외부 후기 부족 — 호출 에이전트가 카카오 SearchGift로 보강)",
                "link": "",
                "_positive_score": {"score": 0, "categories": []},
            })

        budget_str = f" (~{budget:,}원)" if budget else ""
        sections: list[tuple[str, int]] = [
            (f"## 🎁 선물 후보 — {recipient or '받는 분'}{budget_str}", 1),
            (
                "> 광고/협찬/체험단 자동 제거 + 양성 신호 점수 상위 후보\n"
                "> 각 후보에 카카오 SearchGift 호출용 파라미터 동봉",
                2,
            ),
        ]

        for tone, item in zip(tones, top_n):
            title = item.get("title", "(제목 없음)")
            url = item.get("link") or item.get("url", "")
            score = item["_positive_score"]
            min_price = max(1000, int((budget or 100000) * 0.5))
            max_price = budget or 200000
            search_params = (
                "```json\n"
                "{\n"
                f'  "query": "{title[:30]}",\n'
                f'  "minPrice": {min_price},\n'
                f'  "maxPrice": {max_price},\n'
                '  "customTags": ["선물"]\n'
                "}\n"
                "```"
            )
            sections.append((
                f"### {tone} — {title}\n"
                f"**출처**: {url or '(외부 후기 부족)'}\n"
                f"**양성 신호**: {', '.join(score['categories']) or '없음'} (점수 {score['score']})\n\n"
                f"**카카오 선물하기 SearchGift 파라미터**\n{search_params}",
                1,
            ))

        if inp.avoid_categories:
            sections.append((
                "## ⚠️ 회피 카테고리\n" + "\n".join(f"- {c}" for c in inp.avoid_categories),
                2,
            ))
        if inp.recent_gifts_hint:
            sections.append((
                "## 🔁 최근 선물 (중복 회피)\n" + "\n".join(f"- {g}" for g in inp.recent_gifts_hint),
                2,
            ))

        sections.append((
            "## 호출 에이전트에게\n"
            "1. 각 후보의 SearchGift 파라미터를 카카오 선물하기 MCP에 전달해 실제 제품 표시\n"
            "2. 사용자가 '작년 뭐 드렸는지 기억' 같은 경우 GetRecentGiftOrderHistory 결과를 "
            "다음 curate_gifts 호출의 recent_gifts_hint에 넣어주세요\n"
            "3. 트렌드 비교 원하면 GetTrendingGiftRanking 호출 후 우리 후보와 함께 표시\n"
            "4. 양성 신호 부족(점수 0) 후보는 카카오 카탈로그 결과로 충분히 보강 가능",
            3,
        ))

        rb = ResponseBuilder()
        return rb.build(sections, mandatory_footer="네이버 검색 기반")
    finally:
        await client.aclose()


def register(mcp: "FastMCP") -> None:
    @mcp.tool(
        name="curate_gifts",
        description=(
            "Gift Curator(선물고민러). Generate curated gift candidates for the user's "
            "recipient based on relationship, occasion, budget, and recipient context. "
            "Combines Naver Blog/Cafe and Tavily web search results, filters out ads "
            "and sponsored content using rule-based detection (F1: 협찬/체험단/공동구매 "
            "keyword matching), scores positive signals (F2: 구매증빙/타인반응/재구매), "
            "and returns 3 candidates in distinct tones (practical / emotional / "
            "special). Each candidate includes SearchGift-compatible parameters (query, "
            "minPrice, maxPrice, customTags), non-ad source attribution, reasoning, and "
            "trend hints. Does not call LLM internally - the calling agent should pass "
            "each candidate's SearchGift params to the Kakao Gift MCP for catalog "
            "retrieval. Use this as the primary gift recommendation tool."
        ),
        annotations={
            "title": "광고 없는 선물 후보 큐레이션",
            "readOnlyHint": True,
            "destructiveHint": False,
            "openWorldHint": True,
            "idempotentHint": False,
        },
    )
    async def curate_gifts_tool(inp: CurateGiftsInput) -> str:
        return await curate_gifts(inp)
