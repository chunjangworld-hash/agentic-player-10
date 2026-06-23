from shared.ad_filter import AdFilter


def test_detects_explicit_ad_keyword():
    f = AdFilter()
    assert f.is_ad("이거 #광고 표시 있어요") is True
    assert f.is_ad("유료광고 포함 후기") is True


def test_detects_experience_team():
    f = AdFilter()
    assert f.is_ad("체험단으로 받은 제품 후기") is True
    assert f.is_ad("원고료 받고 작성") is True


def test_detects_sponsorship_disclosure():
    f = AdFilter()
    assert f.is_ad("업체로부터 제공받아 작성") is True


def test_clean_text_is_not_ad():
    f = AdFilter()
    assert f.is_ad("정말 좋은 제품이네요. 무릎이 편해졌어요.") is False


def test_filter_keeps_clean_items():
    f = AdFilter()
    items = [
        {"title": "후기 1", "description": "정말 좋아요"},
        {"title": "후기 2", "description": "체험단으로 받았어요"},
        {"title": "후기 3", "description": "재구매 의사 있음"},
    ]
    clean = f.filter_items(items)
    assert len(clean) == 2
    titles = [c["title"] for c in clean]
    assert "후기 1" in titles
    assert "후기 3" in titles


def test_multi_source_score():
    """F4 — 같은 키워드를 여러 출처에서 언급 → 신뢰도 ↑"""
    f = AdFilter()
    items = [
        {"title": "수면 안마기 좋아요", "link": "https://blog.a.com/1", "description": "추천"},
        {"title": "수면 안마기 만족", "link": "https://blog.b.com/2", "description": "최고"},
        {"title": "수면 안마기 별로", "link": "https://blog.a.com/3", "description": "음"},
        {"title": "수면 안마기 굳", "link": "https://cafe.c.com/4", "description": "사용 후기"},
    ]
    scored = f.aggregate_by_source(items, keyword="수면 안마기")
    assert scored["unique_sources"] == 3
    assert scored["total_mentions"] == 4
    assert scored["trust_score"] >= 2
