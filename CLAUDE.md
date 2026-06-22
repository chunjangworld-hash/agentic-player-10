# Project Guidelines — AGENTIC PLAYER 10

## 사용자의 협업 지침 (5가지)

1. **Fancy & 프로페셔널** — 공모전 출품. 목표: 본선 진출 + 입상. 모든 산출물(명세/카피/UI/코드)에 아마추어 톤 금지. 입상 의식해서 매 결정.
2. **델리게이션 타이밍 명시** — GPT/Gemini로 돌릴 시점이 보이면 명시적으로 제안. Claude는 추론·설계·프로젝트 컨텍스트 결정에 reserve.
3. **빈번한 검증** — 명세 섹션마다 시나리오 dry-run, Tool 구현마다 단위 테스트, Phase 끝마다 end-to-end. "내가 본 다음에" 합격.
4. **전문 작업 + 쉬운 설명** — 명세 풀스펙으로 작성하되, 사용자에게 전달할 때는 "왜 + 다음 할 일" 한 줄 정리.
5. **계속 개선** — Phase별 회고. 필요 시 서브에이전트로 병행 탐색 (광고필터/UI 트렌드 등). 마감 직전까지 더 좋은 방향 찾기 멈추지 않음.

## 프로젝트 컨텍스트

- **공모전**: 카카오 AGENTIC PLAYER 10
- **예선 마감**: 2026-07-14 (오늘 기준 25일 남음)
- **출품**: 효도비서 (MCP #1) + 선물고민러 (MCP #2)
- **사용자**: 비개발자, MCP 첫 배포, 풀타임 가용

## 작업 스타일

- 명세는 `docs/specs/` 아래 마크다운으로
- 의사결정/대안 비교는 항상 기록 (왜 그 선택을 했는지)
- 메모리 시스템 활용 — `[[project_agentic_player_10]]`, `[[feedback_collaboration_style]]` 참조
- iterative-engineering 원칙 적용:
  - 수술적 변경
  - 단계별 검증
  - 도구 기본값 의심
  - 암묵적 의존성 명시
- "verify before claim" — 완료 주장 전 실제 동작 확인

## 핵심 기술 스택 (확정 후 갱신)

- MCP 프로토콜: Streamable HTTP, Stateless, Remote
- 인증: 없음 (1차 MVP)
- 서버: Python (FastAPI 또는 공식 MCP Python SDK)
- 배포: **PlayMCP in KC (카카오클라우드)** — Git 소스 빌드 방식
  - Dockerfile 필수, 저장소 루트에 위치
  - 권장: Public GitHub repo 2개 (서비스별)
  - 발급 기간: ~2026-07-14만 가능
  - 등록 데드라인: 7/10 권장 (안전 버퍼)
- 외부: Tavily/Brave Web Search MCP (선물고민러용)

## 입력 모달리티 (확정)

- 카카오톡 ChatGPT 챗봇은 **텍스트 입력만 지원** (이미지/음성 첨부 불가)
- 모든 Tool input은 string 기반
- 이미지를 사용자가 제공해야 하는 시나리오는 "OCR 후 텍스트 붙여넣기" 안내로 우회

## Forward Compatibility 원칙

- **Tool input schema에 미래 확장 필드를 옵셔널로 미리 정의**해두기
- 예: 현재는 `text: string`만 사용. 향후 카카오톡이 이미지 입력 지원하면 `image_base64?: string` 활용
- 카카오톡/PlayMCP 스펙이 진화할 가능성이 높으므로 schema는 보수적이되 확장 가능하게

## 금지 사항 (PlayMCP 가이드 위반 시 심사 반려)

- MCP Server Name / Tool Name에 "kakao" 단어 금지 (대소문자 구분 X, prefix/suffix/중간 포함 모두 불가)
- Tool 응답에 광고 노출 유도 금지
- 개인정보 저장 금지 (1차 MVP)
- "100% 신청 가능" 같은 확정 표현 금지 (False positive 책임)
- API 응답을 raw로 반환 금지 → 정제된 마크다운 형식

## 성능 요건 (필수) ⚠️

- Tool 평균 응답속도: **100ms 이내**
- Tool p99 응답속도: **3,000ms 이내 필수**
- → LLM 호출을 우리 MCP 서버 내에서 하지 말고, 데이터 조회/포맷팅 중심으로 설계
- → 무거운 추론은 Kakao Tools의 호출 에이전트(GPT/Claude)가 처리하도록 위임

## Tool 명세 필수 항목

- `name` (1~128자, A-Za-z0-9_- 만, case-sensitive, 중복 불가)
- `description` (영문 권장, 서비스명 영문+국문 병기, 1024자 이내)
  - 효도비서 → "Hyodo Secretary(효도비서)"
  - 선물고민러 → "Gift Curator(선물고민러)"
- `inputSchema`
- `annotations` (5개 모두 명시):
  - `title`
  - `readOnlyHint`
  - `destructiveHint`
  - `openWorldHint`
  - `idempotentHint`

## Tool 결과 형식

- Result 크기 최소화
- **Response 24,000자 초과 시 에러 → 반려**
- 에러 또는 widget JSON이 아닌 경우 → 정제된 마크다운 텍스트
- API 응답 raw 반환 금지

## 차별가치 입증 의무

- "LLM 자체 웹 검색으로 충분히 구현 가능한 기능만 제공" → 심사 반려
- 우리 정당성: 카카오 자체 MCP (선물하기/나챗방) 조율 + 카카오 생태계 통합 큐레이션
- 명세서/등록 설명에 이 차별 가치 명시 필수

## 명세서 등록 시 확인 사항

- 영업일 기준 7일 심사 (평균 1~2일) → 7/7~7/10 등록 권장 (보완 대응 버퍼)
- 대표 이미지: 정적 PNG만, 고품질 (Phase 3에 제작)
- Resource/Prompt 기능 미사용 (PlayMCP가 다루지 않음)
- 이름에 `AI`/`Bot`/`Service` 같은 중복 키워드 지양 ("효도비서" "선물고민러" OK)
- 개인정보 절대 미요구: 주민번호, 운전면허, 여권번호, 외국인등록번호, 카드번호, 계좌번호
