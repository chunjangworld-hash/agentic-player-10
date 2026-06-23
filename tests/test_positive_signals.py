from shared.positive_signals import PositiveSignalScorer


def test_no_signal_returns_zero():
    s = PositiveSignalScorer()
    r = s.score("아무 의미 없는 일반 문장입니다.")
    assert r["score"] == 0
    assert r["category_count"] == 0
    assert r["categories"] == []


def test_single_strong_keyword_one_category():
    """1 카테고리만 hit — 단일 신호 = 약함."""
    s = PositiveSignalScorer()
    r = s.score("이거 영수증 첨부해서 올립니다. 좋아요.")
    assert r["category_count"] == 1
    assert "purchase_proof" in r["categories"]
    assert r["score"] == 1  # triangular(1) = 1


def test_weak_only_signal_low_score():
    """내돈내산 단독 = 약 신호, 카테고리 hit 없음 + 0.3점 보조."""
    s = PositiveSignalScorer()
    r = s.score("내돈내산입니다 ㅎㅎ")
    assert r["category_count"] == 0
    assert r["weak_signal_count"] == 1
    assert r["score"] == 0.3


def test_two_category_combo():
    """2 카테고리 = 3점 (triangular jump)."""
    s = PositiveSignalScorer()
    # purchase_proof + repurchase_recommendation
    text = "제 돈 주고 샀어요. 재구매했습니다."
    r = s.score(text)
    assert r["category_count"] == 2
    assert r["score"] == 3
    assert set(r["categories"]) == {"purchase_proof", "repurchase_recommendation"}


def test_four_category_top_combo():
    """사용자가 강조한 황금 조합: 구매증빙 + 장기사용 + 단점언급 + 재구매 = 10."""
    s = PositiveSignalScorer()
    text = (
        "직접 구매했습니다. "
        "한 달 써보고 남겨요. "
        "단점은 있지만 만족이에요. "
        "재구매했습니다."
    )
    r = s.score(text)
    assert r["category_count"] == 4
    assert r["score"] == 10  # 4*5/2
    assert set(r["categories"]) == {
        "purchase_proof",
        "daily_usage_pattern",
        "emotion_expression",
        "repurchase_recommendation",
    }


def test_same_category_multiple_keywords_no_stuffing():
    """같은 카테고리에서 키워드 여러 개 매치해도 카테고리 hit는 1."""
    s = PositiveSignalScorer()
    # purchase_proof 카테고리에서만 3개 키워드 동시 매치
    text = "영수증 첨부 합니다. 결제내역 캡처도 있어요. 주문내역 인증 가능."
    r = s.score(text)
    assert r["category_count"] == 1
    assert r["score"] == 1  # 단일 카테고리는 그대로 1점


def test_plus_keyword_requires_both_substrings():
    """'내돈내산 + 주문내역' (중) 키워드는 두 substring 모두 있어야 매치."""
    s = PositiveSignalScorer()
    # 둘 다 있음 → 중 신호로 purchase_proof 카테고리 hit
    text = "내돈내산입니다. 주문내역 첨부해요."
    r = s.score(text)
    # purchase_proof 매치 (중 신호도 카테고리 hit)
    assert "purchase_proof" in r["categories"]

    # 하나만 있으면 약 신호('내돈내산')만 매치 → 카테고리 hit 없음
    s2 = PositiveSignalScorer()
    r2 = s2.score("내돈내산입니다.")
    assert r2["category_count"] == 0
    assert r2["weak_signal_count"] >= 1


def test_assess_items_attaches_scores():
    """리스트 입력 시 각 item에 _positive_score 키 부착."""
    s = PositiveSignalScorer()
    items = [
        {"title": "A", "description": "내돈내산이고 재구매했습니다. 한 달 써보고 남겨요."},
        {"title": "B", "description": "일반 후기."},
    ]
    out = s.assess_items(items)
    assert len(out) == 2
    assert out[0]["_positive_score"]["score"] >= 3  # 2+ 카테고리
    assert out[1]["_positive_score"]["score"] == 0
