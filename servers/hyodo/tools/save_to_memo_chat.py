"""save_to_memo_chat — 효도비서 결과를 카카오 나챗방 저장용 텍스트로 포맷팅.

⚠️ 우리는 MemoChat MCP를 직접 호출하지 않음. 포맷팅만.
응답 예산: <10ms.
"""
from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from shared.input_coercion import coerce_to_string
from shared.response_builder import ResponseBuilder


class SaveToMemoChatInput(BaseModel):
    content: str = Field(..., min_length=1, max_length=5000)
    category: Literal["anbu", "warning", "event", "general"] = "general"
    label: str | None = Field(None, max_length=100)

    @field_validator("content", "label", mode="before")
    @classmethod
    def _coerce_strings(cls, v):
        return coerce_to_string(v)


_CATEGORY_KOR = {
    "anbu": "안부",
    "warning": "경고",
    "event": "이벤트",
    "general": "일반",
}


def save_to_memo_chat(inp: SaveToMemoChatInput) -> str:
    today = date.today().isoformat()
    category_kor = _CATEGORY_KOR[inp.category]
    label_part = f" | [라벨: {inp.label}]" if inp.label else ""

    header = f"📌 효도비서 — [카테고리: {category_kor}]{label_part}"
    date_line = f"📅 {today}"
    body = inp.content

    footer = (
        "\n\n## 호출 에이전트에게\n"
        "위 텍스트 블록을 카카오톡 나챗방 MCP의 MemoChat tool에 message 파라미터로 "
        "전달해주세요. 우리 효도비서는 직접 MemoChat을 호출하지 않습니다."
    )

    rb = ResponseBuilder()
    return rb.build([
        ("## MemoChat에 저장할 텍스트", 1),
        ("---", 1),
        (header, 1),
        (date_line, 1),
        (body, 1),
        ("---", 1),
        (footer, 2),
    ])


def register(mcp) -> None:
    """FastMCP Tool 등록. server.py의 register_all(mcp)에서 호출."""

    @mcp.tool(
        name="save_to_memo_chat",
        description=(
            "Hyodo Secretary(효도비서). Use this when the user explicitly asks to save "
            "a Hyodo Secretary result for later reference in a personal memo chat or "
            "to hand it off to MemoChat. Formats an existing greeting, warning, event "
            "reminder, or parent-note output into a concise Korean text block with "
            "title, date cue, source context, and action tags. This tool does not "
            "store data or call MemoChat directly; it is LLM-free and only applies "
            "deterministic formatting rules so the calling agent can pass the returned "
            "text to a memo-saving tool."
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
