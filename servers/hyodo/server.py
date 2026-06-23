"""Hyodo Secretary(효도비서) MCP Server.

⚠️ Phase 2.1: 골격만. Tool은 Phase 2.2에서 추가.

포트:
- 기본 8000. 환경변수 FASTMCP_PORT 로 오버라이드 (Docker/카카오클라우드 배포 호환).
- 로컬에서 선물고민러와 동시 실행 시 자동 분리 (각자 다른 디폴트).
"""
from __future__ import annotations

import os

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
    port=int(os.environ.get("FASTMCP_PORT", 8000)),
    host=os.environ.get("FASTMCP_HOST", "127.0.0.1"),
)


# Tool 등록 — Phase 2.2에서 점진적으로 추가
from servers.hyodo.tools.save_to_memo_chat import SaveToMemoChatInput, save_to_memo_chat


@mcp.tool(
    description=(
        "Hyodo Secretary(효도비서). Format a Hyodo Secretary result "
        "(greeting message, scam warning, event reminder) into a clean text "
        "block ready for saving to the user's KakaoTalk MemoChat (나와의 채팅방). "
        "Returns the formatted text only. Does not call MemoChat MCP directly - "
        "the calling agent should pass this output to MemoChat MCP's MemoChat tool. "
        "Use this when the user explicitly wants to save a Hyodo Secretary result for later reference."
    ),
    annotations={
        "title": "결과를 나챗방에 저장",
        "readOnlyHint": True,
        "destructiveHint": False,
        "openWorldHint": False,
        "idempotentHint": True,
    },
)
def save_to_memo_chat_tool(inp: SaveToMemoChatInput) -> str:
    return save_to_memo_chat(inp)


def main() -> None:
    """서버 진입점 — Streamable HTTP 모드로 실행."""
    logger.info("hyodo_server_starting")
    mcp.run(transport="streamable-http")


if __name__ == "__main__":
    main()
