# Phase 2.2 시나리오 카드 — 외주 결과

## 출처
2026-06-23 GPT-5 + Gemini 외주 #2 결과. 각 30개씩 총 60개 시나리오.

## 파일
- `phase2.2-gpt.json` — 30개 (schema 일관성 우수, baseline)
- `phase2.2-gemini.json` — 30개 (발화 다양성·엣지케이스 보강)

## 활용 방법

### Phase 2.2 명세 작성 시
1. **Tool input pydantic schema** = GPT 결과의 input fields를 baseline으로
2. **각 Tool description의 edge case 가이드라인** = Gemini의 edge_case_notes 흡수
3. **Tool TDD 케이스** = 두 결과에서 핵심 시나리오 10~15개를 input/expected_output 쌍으로 변환

### 핵심 인사이트
- 관계 다양성 7+ (엄마/아빠/시어머니/시아버지/친정엄마/친정아빠/장모님/장인어른/할머니)
  → `relation` 필드는 enum이 아닌 자유 텍스트
- Tool 연쇄 패턴 8~10개 시나리오 → description에 "함께 호출되는 Tool" 힌트 포함
- 공통 safety filter 필요 (의료/금융 확정 표현 금지) → 향후 `shared/safety_disclaimer.py` 후보
- 이미지 입력 시나리오는 OCR 텍스트 변환 안내로 우회

### 검증된 설계 결정
- F2 양성 신호 5 카테고리 (purchase_proof / third_party_reaction / repurchase_recommendation / emotion_expression / daily_usage_pattern)
  → 사용자 발화에 자연스럽게 등장하는 키워드와 일치. 설계 정확성 입증.
