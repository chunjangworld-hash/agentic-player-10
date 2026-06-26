"""Phase 2.6 — UX 흐름·fancy 톤 가이드가 Tool 응답에 포함되는지 검증.

마켓 AI 채팅에서 발견한 톤 문제:
- 응답이 백과사전·교과서 톤
- 끝에 "이 메시지는 ...입니다" 같은 메타 해설
- 사용자 선택지 (옵션 카드) 없음

해결: Tool 응답 자체에 LLM 행동 가이드를 inline으로 박음.
이 모듈은 그 가이드가 정확히 들어갔는지 + 응답 길이가 22k 한도 안인지 검증.
"""
from __future__ import annotations

from servers.hyodo.tools.check_suspicious_message import (
    CheckSuspiciousMessageInput,
    check_suspicious_message,
)
from servers.hyodo.tools.compose_anbu import ComposeAnbuInput, compose_anbu


# compose_anbu — fancy 톤 가이드

def test_compose_anbu_response_has_fancy_tone_guide():
    result = compose_anbu(
        ComposeAnbuInput(parent_brief="엄마 65세 어깨 수술 등산 좋아함")
    )
    assert "fancy 톤 원칙" in result
    assert "메타 해설 절대 금지" in result
    assert "이모지 0-1개" in result


def test_compose_anbu_response_has_user_choice_card():
    """메시지 작성 후 사용자에게 보여줄 옵션 카드가 응답에 포함."""
    result = compose_anbu(
        ComposeAnbuInput(parent_brief="아빠 70대 골프")
    )
    assert "다른 결로 다시" in result
    assert "다른 주제로 다시" in result
    assert "나챗방에 저장" in result
    # 옵션 카드 이모지
    assert "🔄" in result
    assert "🎯" in result
    assert "💾" in result


def test_compose_anbu_response_has_example_outputs():
    """LLM이 fancy 톤 잡도록 예시 4종 제공."""
    result = compose_anbu(
        ComposeAnbuInput(parent_brief="엄마 60대 무릎")
    )
    assert "예시 결" in result
    # 예시 4종 키워드
    assert "장마" in result or "트로트" in result or "보고싶다" in result or "망종" in result


def test_compose_anbu_response_reflects_user_chosen_tone():
    """사용자가 고른 톤(playful)이 가이드에 명시되는지."""
    result = compose_anbu(
        ComposeAnbuInput(parent_brief="엄마 60대", tone="playful")
    )
    assert "`playful`" in result or "playful" in result
    assert "가벼움" in result or "장난" in result


def test_compose_anbu_response_under_22k_limit():
    """응답 길이가 PlayMCP 24k 한도(우리 안전선 22k) 안."""
    result = compose_anbu(
        ComposeAnbuInput(
            parent_brief="엄마 60대 무릎 안 좋고 등산 좋아함 손주 자주 봄",
            occasion="환절기 비 오는 날",
        )
    )
    assert len(result) < 22000, f"응답 길이 {len(result)} > 22000 한도"


# check_suspicious_message — 위험도별 옵션 카드

def test_check_suspicious_response_has_action_guide():
    result = check_suspicious_message(
        CheckSuspiciousMessageInput(message_text="긴급 대출 승인 확인 클릭 https://fake.example/click")
    )
    assert "사용자 응답 톤" in result or "다음 액션 지침" in result
    assert "100% 사기" in result  # 단정 표현 회피 가이드
    assert "메타 해설" in result


def test_check_suspicious_response_has_option_card():
    """위험도 중간 이상이면 보여줄 옵션 카드 가이드 포함."""
    result = check_suspicious_message(
        CheckSuspiciousMessageInput(
            message_text="택배 미수령 확인 https://parcel-check.example/track"
        )
    )
    assert "부모님께 보낼 경고 카드" in result
    assert "나챗방에 저장" in result
    assert "다른 메시지도 검토" in result
    # 옵션 카드 이모지
    assert "📨" in result
    assert "💾" in result
    assert "🔍" in result


def test_check_suspicious_response_under_22k_limit():
    result = check_suspicious_message(
        CheckSuspiciousMessageInput(
            message_text="긴급 대출 승인 확인 클릭 " + "https://fake.example " * 50
        )
    )
    assert len(result) < 22000, f"응답 길이 {len(result)} > 22000 한도"


def test_check_suspicious_response_low_risk_has_safe_guidance():
    """낮은 위험도일 때도 일반 예방 안내가 포함."""
    result = check_suspicious_message(
        CheckSuspiciousMessageInput(message_text="안녕하세요 잘 지내시죠?")
    )
    assert "1577-0001" in result or "KISA" in result or "118" in result
