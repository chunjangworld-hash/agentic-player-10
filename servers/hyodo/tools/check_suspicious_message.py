"""check_suspicious_message — 의심 메시지 사기 패턴 룰 매칭.

응답 예산: <100ms. 정적 사기 패턴 DB + URL 도메인 비교 + 키워드 매칭.
LLM 호출 없음 — 룰 기반 빠른 위험 신호 추출만, 최종 판단은 호출 에이전트.
"""
from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING
from urllib.parse import urlparse

from pydantic import BaseModel, Field, field_validator

from shared.input_coercion import coerce_to_string
from shared.response_builder import ResponseBuilder

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

_DATA_DIR = Path(__file__).resolve().parent.parent / "data"
_URL_RE = re.compile(r"https?://[^\s]+", re.IGNORECASE)
_PRESSURE_KWS = ("즉시", "오늘 안", "지금 당장", "3분 안에", "1시간 안", "분 안에")
_SHORTENER_HOSTS = ("bit.ly", "tinyurl.com", "is.gd", "buly.kr", "han.gl", "t.co")

# 한국 주요 브랜드 영문 별칭 — 합법 도메인엔 들어 있지 않지만
# 피싱 도메인은 흔히 이 단어를 본떠 만듦 (예: kookmin1n.com → KB국민은행 사칭)
_BRAND_ALIASES = (
    "kookmin",   # 국민은행 (정식 도메인은 kbstar.com)
    "kakaopay",  # 카카오페이
    "naverpay",  # 네이버페이
    "samsungpass",
    "coupang",
    "lottecard",
    "shinhan",   # shinhan.com 정식이지만 typo (예: shlnhan, shinhann) 잡힘
    "wooribank",
    "hanabank",
    "nonghyup",
    "kakaobank",
    "tossbank",
)

# risk_level 한글 → 점수 가중치
_RISK_WEIGHT = {
    "매우 높음": 35,
    "높음": 25,
    "중간": 15,
    "낮음": 8,
}


class CheckSuspiciousMessageInput(BaseModel):
    message_text: str = Field(
        ...,
        min_length=1,
        max_length=3000,
        description="검사할 메시지 본문 (카카오톡/SMS 텍스트, OCR 결과, 또는 자연어 설명).",
    )
    sender_info: str | None = Field(
        None,
        max_length=200,
        description="발신자 전화번호·이름 등 (선택). 참고용으로만 응답에 표시.",
    )
    image_base64: str | None = Field(
        None,
        description="향후 카카오톡이 이미지 입력 지원 시 사용. 현재 사용 안 함.",
    )

    @field_validator("message_text", "sender_info", "image_base64", mode="before")
    @classmethod
    def _coerce_strings(cls, v):
        return coerce_to_string(v)


@lru_cache(maxsize=1)
def _load_scam_patterns() -> dict:
    with open(_DATA_DIR / "scam_patterns.json", encoding="utf-8") as fp:
        return json.load(fp)


@lru_cache(maxsize=1)
def _load_legit_domains() -> list[str]:
    with open(_DATA_DIR / "legit_domains.json", encoding="utf-8") as fp:
        data = json.load(fp)
    domains: list[str] = []
    for k, v in data.items():
        if k.startswith("_"):
            continue
        if isinstance(v, list):
            domains.extend(v)
    return domains


def _extract_urls(text: str) -> list[str]:
    return _URL_RE.findall(text)


def _check_url(url: str, legit_domains: list[str]) -> tuple[bool, str | None, str]:
    """오타 도메인 검출 + 단축 URL 검출. returns (is_suspicious, hint_message, host)."""
    try:
        netloc = urlparse(url).netloc.lower()
    except ValueError:
        return False, None, ""

    if not netloc:
        return False, None, ""

    if any(s in netloc for s in _SHORTENER_HOSTS):
        return True, f"단축 URL ({netloc}) — 목적지 불명", netloc

    # 정확히 일치하거나 합법 도메인의 서브도메인이면 통과
    for legit in legit_domains:
        if netloc == legit or netloc.endswith("." + legit):
            return False, None, netloc

    # 합법 도메인의 root 단어가 들어 있지만 정확히는 아닌 경우 → 오타 의심
    for legit in legit_domains:
        legit_root = legit.split(".")[0]
        if len(legit_root) >= 4 and legit_root in netloc:
            return True, f"오타 도메인 의심 — 진짜 `{legit}` 와 다름", netloc

    # 한국 주요 금융·결제 브랜드 별칭이 들어간 도메인 (예: kookmin1n.com)
    for alias in _BRAND_ALIASES:
        if alias in netloc:
            return True, (
                f"한국 금융·결제 브랜드명 `{alias}` 사용 — 공식 도메인 아님"
            ), netloc

    return False, None, netloc


def check_suspicious_message(inp: CheckSuspiciousMessageInput) -> str:
    scam_data = _load_scam_patterns()
    legit_domains = _load_legit_domains()
    text = inp.message_text

    risk_score = 0
    signals: list[str] = []
    matched_types: list[str] = []

    # URL 검사
    for url in _extract_urls(text):
        is_susp, hint, host = _check_url(url, legit_domains)
        if is_susp:
            risk_score += 40
            signals.append(f"의심 URL `{host}` — {hint}")

    # 키워드 매칭 (사기 패턴 사전)
    # JSON shape: {patterns: [{type_name, keywords, url_patterns, risk_level, ...}]}
    patterns = scam_data.get("patterns", [])
    for entry in patterns:
        if not isinstance(entry, dict):
            continue
        kws = entry.get("keywords", [])
        if not isinstance(kws, list):
            continue
        hit = [kw for kw in kws if isinstance(kw, str) and kw in text]
        if hit:
            risk_level = entry.get("risk_level", "중간")
            weight = _RISK_WEIGHT.get(risk_level, 15)
            risk_score += weight
            type_name = entry.get("type_name", "사기 유형 미상")
            matched_types.append(f"{type_name} (위험도 {risk_level})")
            signals.append(
                f"사기 키워드 ({type_name}): {', '.join(hit[:3])}"
            )

    # 시간 압박 패턴
    pressure_hits = [kw for kw in _PRESSURE_KWS if kw in text]
    if pressure_hits:
        risk_score += 15
        signals.append(f"시간 압박 표현: {', '.join(pressure_hits)}")

    # 위험도 판정
    if risk_score >= 50:
        verdict = "**매우 높음**"
    elif risk_score >= 25:
        verdict = "**중간**"
    elif risk_score > 0:
        verdict = "낮음"
    else:
        verdict = "위험 신호 없음"

    sections: list[tuple[str, int]] = [
        (f"## 위험도 판정\n{verdict} (점수 {risk_score})", 1),
    ]
    if signals:
        sections.append((
            "## 발견된 위험 신호\n" + "\n".join(f"- {s}" for s in signals),
            1,
        ))
    if matched_types:
        sections.append((
            "## 매칭된 사기 유형\n"
            + "\n".join(f"- {m}" for m in matched_types),
            1,
        ))
    if inp.sender_info:
        sections.append((f"## 발신자 정보 (참고)\n- {inp.sender_info}", 2))

    sections.append((
        "## 권장 대응 단계\n"
        "1. **절대 링크 클릭 X**\n"
        "2. 부모님께 즉시 전달 → 클릭 안 했는지 확인\n"
        "3. 만약 클릭/정보 입력했다면 카드/계좌 정지(1577-0001) + KISA 신고(118)",
        2,
    ))
    sections.append((
        "## 호출 에이전트에게\n"
        "위 신호들을 종합해 자녀에게 명확하고 침착한 어조로 사기 가능성과 "
        "즉시 해야 할 행동을 설명해주세요. 부모님께 보낼 경고 메시지가 필요하면 "
        "compose_parent_warning Tool을 추가 호출하세요.",
        3,
    ))

    rb = ResponseBuilder()
    return rb.build(sections)


def register(mcp: "FastMCP") -> None:
    """FastMCP Tool 등록."""

    @mcp.tool(
        name="check_suspicious_message",
        description=(
            "Hyodo Secretary(효도비서). Use this when the user provides a suspicious "
            "Korean message, OCR text, sender clue, URL, or natural-language "
            "description of something a parent received and asks whether it may be "
            "scam, phishing, or smishing. Returns matched risk signals, scam-type "
            "labels, URL/sender red flags, confidence band, and recommended next "
            "actions for the calling agent to explain. It does not write a warning "
            "to the parent; call compose_parent_warning next if forwarding guidance "
            "is needed. LLM-free: rule-based matching against a curated Korean "
            "scam-pattern database."
        ),
        annotations={
            "title": "의심 메시지 사기 판단",
            "readOnlyHint": True,
            "destructiveHint": False,
            "openWorldHint": False,
            "idempotentHint": True,
        },
    )
    def check_suspicious_message_tool(inp: CheckSuspiciousMessageInput) -> str:
        return check_suspicious_message(inp)
