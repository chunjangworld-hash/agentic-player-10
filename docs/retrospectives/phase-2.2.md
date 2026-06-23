# Phase 2.2 회고 (2026-06-23)

## 결과 한 줄
효도비서 5 Tool + 선물고민러 5 Tool 모두 구현 + FastMCP 등록 완료. 92 testcases 통과. 18 commits on `phase-2.2`. **subagent-driven 방식 첫 적용** — 14 Task 중 11개 완료, Task 12(외주 #4)는 외주 결과 대기.

## 측정 가능한 성과
- **92 testcases · 100% pass · ~1.2s** 전체 수행
- **10 Tools** registered:
  - 효도비서: save_to_memo_chat, compose_parent_warning, compose_anbu, find_upcoming_events, check_suspicious_message
  - 선물고민러: compose_gift_message, find_real_recommendations, evaluate_gift_idea, curate_gifts, refine_recommendation
- **18 commits** on `phase-2.2` (Tool 11개 + 패턴 fix 3개 + 데이터 1개 + safety_filter 1개 + plan/회고 2개)
- **4개 새 데이터 파일**: seasonal_events / health_seasonal_risks / legit_domains / tone_templates
- **1개 새 shared 모듈**: `shared/safety_filter.py` (의료/금융/사기 disclaimer)

## 핵심 설계 결정 (subagent 실행 중 확립)

### 1. Aggregator 패턴 (Task 2 → 모든 후속에 강제)
초기 Task 2에서 Tool registration을 server.py에 직접 박은 코드를 quality review가 catch.
→ `servers/<server>/tools/__init__.py::register_all(mcp)` 신설, 각 Tool 모듈은 `register(mcp)` 함수 노출.
→ **server.py는 단 한 줄(`register_all(mcp)`)만 호출** — 새 Tool 추가 시 server.py 절대 안 건드림.
→ 효과: Task 3~11 추가 시 모두 동일 패턴, 충돌 0회.

### 2. `@mcp.tool(name="...")` 명시 (Task 3 quality review에서 Critical 발견)
초기 default behavior — 함수명이 그대로 노출 Tool 이름.
→ 결과: `save_to_memo_chat_tool` (Phase 1 spec는 `save_to_memo_chat`).
→ Fix: `@mcp.tool(name="save_to_memo_chat", ...)` 명시. 이후 모든 Tool 동일.
→ 효과: PlayMCP 등록 명세와 100% 일치, "kakao" prefix 금지 규정도 자동 보장.

### 3. JSON shape 사전 probe (Tasks 4·5·6·7에서 매번 반복)
Implementer subagent가 spec 코드 sketch를 그대로 쓰지 않고, JSON 파일 실제 shape를 먼저 확인 후 적응.
→ 효과: list-of-records vs nested dict 같은 차이로 인한 silent bug 방지.

### 4. Async wrapper + `await` (Task 8 외부 API 첫 등장 시 확립)
```python
async def find_real_recommendations_tool(inp) -> str:
    return await find_real_recommendations(inp)
```
FastMCP가 coroutine을 await — 이 패턴 안 쓰면 응답이 coroutine 객체 그대로 반환.

### 5. `mandatory_footer="네이버 검색 기반"` 자동 부착 (Tasks 8·9·10에서 적용)
Naver API 약관 출처 표기 의무를 `ResponseBuilder.mandatory_footer`가 자동 보장.
→ 호출자가 잊어도 안전.

## Subagent-Driven Development 회고

### 잘된 것
- **Task당 implementer + spec reviewer + quality reviewer 3단계** — 패턴 일관성·spec 위반 catch에 효과적
- **Quality review가 진짜로 critical 이슈 catch**: aggregator 패턴 (Task 2), `_tool` suffix (Task 3) — 둘 다 main context에선 놓쳤을 항목
- **각 task fresh subagent** = context 오염 없음, 일관된 conventions 적용
- **Implementer가 JSON shape를 적응하며 self-correct** — fragile spec 보강

### 어려웠던 것
- **Task 6 중간에 subagent 세션 한도 도달** — fix: 인라인으로 마무리 후 다음 task 진행
- **각 dispatch가 token 비용 큼** — implementer + 2 reviewers = task당 약 60~150k tokens
- **재dispatch 빈도 ↑** (`SendMessage` 미지원으로 매번 fresh agent 호출)
- **Conventions를 모든 dispatch prompt에 명시** — 잊으면 dispatch에 따라 일관성 깨짐

### 개선 방향 (Phase 2.3 이후)
- `SendMessage` 같은 agent resume tool 활용 가능하면 같은 implementer agent에 fix만 추가 지시
- Critical 컨벤션은 plan 본문에 강조 + 매 dispatch prompt 첫 줄에 한 번 더 강조
- Spec/quality review의 token 비용을 줄이기 위해 더 작은 단위 task로 쪼개거나 review 결합

## Phase 2.3 (배포) 진입 전 짚을 것

### 미해결 항목
| # | 항목 | 해결 시점 |
|---|---|---|
| 2.2-U1 | 외주 #4 (Tool 영문 description 풍부화) — 현재 implementer가 spec 영문 그대로 사용. 더 LLM-friendly로 다듬을 여지 | 외주 결과 받은 후 Task 12 |
| 2.2-U2 | shared/safety_filter 통합 미적용 — 의료/금융/사기 disclaimer가 Tool 출력에 안 붙음. 적용 시점 결정 필요 | Phase 2.3 또는 본선 |
| 2.2-U3 | curate_gifts의 톤 분류 (감성/실용/특별) — 현재 단순 점수 순 라벨 부착. 실제 톤 분류 알고리즘 보강 가능 | 본선 Phase 4 |
| 2.2-U4 | recent_gifts_hint 활용 — GetRecentGiftOrderHistory 응답 구조 모름 | 실제 카카오 MCP 호출 후 |
| 2.2-U5 | F4 다중 출처 cross-validation — 현재 단순 도메인 카운트. 더 정교한 weighting 가능 | 시나리오 dry-run으로 검증 후 |
| 2.2-U6 | 응답 시간 실측 미실행 — 100ms 평균 / 3s p99 가이드 대비 실제 성능 | Phase 2.3 통합 테스트 |
| 2.2-U7 | data 파일 일부 항목 누락 (예: `legit_domains.banks`에 새마을금고/우체국예금 미포함) | 외주 또는 Phase 3 polish |
| 2.2-U8 | seasonal_events.json의 날짜 충돌 (06-06 망종/현충일, 05-21 소만/부부의 날) — find_upcoming_events tie-breaker | 다음 buggy 발견 시 |

### 본선(Phase 4) 진입 시 준비
- **Widget 스펙 학습** (메모 reference_playmcp_review_policy 참조)
- **Tool 호출 trace** — MCP Inspector로 실 사용자 시나리오 검증

## 다음 단계 (Phase 2.3)

- **Dockerfile 작성** (외주 #5)
- **카카오클라우드 PlayMCP in KC 등록** (Git 소스 빌드)
- **PlayMCP 마켓 등록** (임시 등록 → AI 채팅 테스트 → 정식 심사)
- **대표 이미지 시안 확정** (외주 #6, Phase 3.1)

기간 추정: Phase 2.3 = 2~3일 (배포 환경 학습 포함).
