"""Hyodo Secretary(효도비서) MCP Server.

⚠️ Phase 2.1: 골격만. Tool은 Phase 2.2에서 추가.
"""
from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from shared.logging import setup_logger

logger = setup_logger("hyodo_server")

mcp = FastMCP(
    "Hyodo Secretary(효도비서)",
    instructions=(
        "효도비서: 부모님과 멀리 사는 자녀를 위한 카카오톡 도우미. "
        "안부 메시지 생성과 의심 메시지 사기 판단이 두 핵심 기능. "
        "모든 Tool은 빠른 데이터 조회/포맷팅만 — 자연어 추론은 호출 에이전트가 담당."
    ),
)


# Tool 등록은 Phase 2.2에서 추가됨
# from servers.hyodo.tools import compose_anbu, check_suspicious_message, ...


def main() -> None:
    """서버 진입점 — Streamable HTTP 모드로 실행."""
    logger.info("hyodo_server_starting")
    mcp.run(transport="streamable-http")


if __name__ == "__main__":
    main()
