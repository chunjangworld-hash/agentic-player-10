# 구현 계획 (Implementation Plans)

**Goal**: 효도비서 + 선물고민러 MCP 서버 2개 구현 → 카카오 PlayMCP 등록 (예선 마감 2026-07-14)

## 4-Phase 구조

| Phase | 기간 | 산출물 | 계획 문서 |
|---|---|---|---|
| **2.1 공유 인프라** | 6/23~6/26 (4일) | shared/* 모듈 + 서버 골격 | [2026-06-22-phase2.1-shared-infrastructure.md](./2026-06-22-phase2.1-shared-infrastructure.md) ✅ |
| **2.2a 효도비서 Tool** | 6/27~7/2 (6일) | 5개 Tool 구현 + 통합 테스트 | (작성 예정 — Phase 2.1 완료 시) |
| **2.2b 선물고민러 Tool** | 7/3~7/8 (6일) | 5개 Tool 구현 + 통합 테스트 | (작성 예정) |
| **2.3 Docker + 배포** | 7/9 (1일) | Dockerfile + PlayMCP in KC 등록 | (Phase 3와 통합) |
| **3 폴리시 + 등록** | 7/10~7/14 (5일) | 대표 이미지 + PlayMCP MCP 등록 | (Phase 2 완료 시) |

## 왜 Phase별로 분리하나

- **Phase 2.1 결과가 Phase 2.2 구현에 영향**을 미침 (인터페이스가 달라질 수 있음)
- 비개발자가 한 번에 다 보면 압도됨
- 단계별 검증 (5가지 협업 지침 #3)
- 각 phase 끝에 회고 → 다음 phase 개선 (5가지 협업 지침 #5)

## 사용 방법

각 phase plan은 **TDD 패턴**으로 작성:
1. 실패하는 테스트 작성
2. 테스트 실패 확인
3. 최소 구현
4. 테스트 통과 확인
5. 커밋

비개발자도 따라할 수 있도록 모든 명령·코드 명시.

## 관련 문서

- `docs/specs/` — Phase 1 명세 (architecture / hyodo / gift-curator)
- `docs/data/` — 데이터 파일 (사기 패턴 / 광고 키워드 등)
- `docs/design/` — 비주얼 아이덴티티
- `CLAUDE.md` — 협업 지침 + 제약 사항
