"""Gift Curator(선물고민러) MCP Server.

⚠️ Phase 2.1: 골격만. Tool은 Phase 2.2에서 추가.
"""
from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from shared.logging import setup_logger

logger = setup_logger("gift_curator_server")

mcp = FastMCP(
    "Gift Curator(선물고민러)",
    instructions=(
        "선물고민러: 광고/협찬 없는 진짜 칭찬받은 선물을 큐레이션하는 도우미. "
        "관계·예산·상황을 바탕으로 카카오 선물하기 MCP의 SearchGift와 자연 연계되는 "
        "키워드·가격대·추천 이유를 반환. 모든 Tool은 데이터 조회/필터링만 담당."
    ),
)


# Tool 등록은 Phase 2.2에서 추가됨


def main() -> None:
    logger.info("gift_curator_server_starting")
    mcp.run(transport="streamable-http")


if __name__ == "__main__":
    main()
