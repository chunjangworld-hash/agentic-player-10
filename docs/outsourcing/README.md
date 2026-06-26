# 외주 워크플로 (Outsourcing)

> Claude 본세션은 추론·설계·프로젝트 컨텍스트 결정에 reserve. 정형화된 카피·코드·이미지는 외주에 위임. 결과물 받으면 본세션에서 통합 검증.

## 외주 매트릭스

| # | 외주 | 위임 대상 | 진행 상태 | 결과물 위치 |
|---:|---|---|---|---|
| #1 | PlayMCP 가이드 확인 | (1차 세션 완료) | ✅ | 메모리 5종 |
| #2 | Phase 2.2 시나리오 60개 | (1차 세션 완료) | ✅ | `docs/scenarios/` |
| #3 | 사전 v2 확장 | (1차 세션 완료) | ✅ | `docs/data/` |
| #4 | Tool description 검수·다듬기 | **GPT-5** (또는 Claude Opus 별도 세션) | 🟠 프롬프트 준비됨 | `2026-06-26-task4-result.json` |
| #5 | Dockerfile 2종 작성 | **GPT-5** (또는 Codex/Cursor) | 🟠 프롬프트 준비됨 | `Dockerfile.hyodo`, `Dockerfile.gift_curator`, `.dockerignore` |
| #6 | 대표 이미지 시안 | **이미지 생성 AI** (Midjourney/DALL-E) | ✅ 2장 확정 | `assets/images/mascots/` |

## 외주 진행 절차

1. **프롬프트 작성** — 본세션이 컨텍스트 풀로 담아 마크다운으로 출력
2. **사용자가 던지기** — 해당 외주 채널(GPT-5 등)에 그대로 복붙
3. **결과 회수** — 사용자가 결과를 본세션에 붙여넣거나 파일로 저장
4. **본세션 통합** — 검수 → 회귀 테스트 → commit

## 프롬프트 인덱스

- [Task #4 — Tool description 검수·다듬기](2026-06-26-task4-tool-descriptions.md)
- [Task #5 — Dockerfile 2종 작성](2026-06-26-task5-dockerfile.md)
