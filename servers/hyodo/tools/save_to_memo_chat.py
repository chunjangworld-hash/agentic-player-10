"""save_to_memo_chat — 효도비서 결과를 카카오 나챗방 저장용 텍스트로 포맷팅.

⚠️ 우리는 MemoChat MCP를 직접 호출하지 않음. 포맷팅만.
응답 예산: <10ms.
"""
from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field

from shared.response_builder import ResponseBuilder


class SaveToMemoChatInput(BaseModel):
    content: str = Field(..., min_length=1, max_length=5000)
    category: Literal["anbu", "warning", "event", "general"] = "general"
    label: str | None = Field(None, max_length=100)


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
