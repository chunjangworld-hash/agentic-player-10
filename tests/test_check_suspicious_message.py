from servers.hyodo.tools.check_suspicious_message import (
    CheckSuspiciousMessageInput,
    check_suspicious_message,
)


def test_loan_scam_high_risk():
    inp = CheckSuspiciousMessageInput(
        message_text="국민은행 대출 승인됐습니다 즉시 https://kookmin1n.com/auth 클릭",
    )
    result = check_suspicious_message(inp)
    # 위험도 표시 + 의심 URL 노출
    assert "높음" in result or "high" in result.lower() or "위험" in result
    assert "kookmin1n" in result
    assert "신고" in result


def test_courier_smishing():
    inp = CheckSuspiciousMessageInput(
        message_text="우체국 반송 물품. 주소 미확인. http://bit.ly/abc123 클릭하여 본인확인",
    )
    result = check_suspicious_message(inp)
    # 단축 URL 또는 택배·사칭 키워드 감지
    assert "위험" in result or "의심" in result or "사칭" in result


def test_clean_message_low_risk():
    inp = CheckSuspiciousMessageInput(
        message_text="엄마, 오늘 비 와요. 우산 챙기세요.",
    )
    result = check_suspicious_message(inp)
    # 위험 신호 없음 또는 낮음
    assert "낮음" in result or "위험 신호 없" in result or "0점" in result or "없음" in result


def test_pressure_keyword_detected():
    inp = CheckSuspiciousMessageInput(
        message_text="즉시 본인 인증 필요. 3분 안에 답변하지 않으면 계정 정지",
    )
    result = check_suspicious_message(inp)
    assert "압박" in result or "즉시" in result or "위험" in result


def test_with_sender_info():
    """sender_info 옵셔널 필드 정상 수신."""
    inp = CheckSuspiciousMessageInput(
        message_text="대출 안내",
        sender_info="+82-10-1234-5678",
    )
    result = check_suspicious_message(inp)
    assert len(result) > 50  # 정상 응답 생성
