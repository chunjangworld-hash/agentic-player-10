# 외주 #4 — Tool description 검수·다듬기

**위임 대상**: GPT-5 (1회 호출, ~5분 작업)
**목표**: 10개 Tool의 영문 `description` 필드를 PlayMCP 심사 통과 + 카카오 GPT/Claude Tool selection 정확도 최대화하도록 검수·개선
**산출물 형식**: 아래 명시한 JSON 1개 (그대로 파일로 저장 가능)
**예상 토큰**: 입력 ~6k, 출력 ~5k

---

## 🚀 외주 프롬프트 (이하 전부 복붙)

```
You are a senior MCP server reviewer specializing in Anthropic Model Context Protocol
tool design. I am submitting two MCP servers (Hyodo Secretary / Gift Curator) to
"PlayMCP in KakaoCloud" — a Korean MCP marketplace whose review board rejects servers
that (a) duplicate functionality already obtainable from the calling LLM's native web
search, (b) violate Korean naming guidelines, or (c) have ambiguous use-case triggers
that cause routing failures in Kakao's GPT/Claude orchestrator.

## Your task

For each of the 10 tools below, review the current English `description` field and
return an improved version that maximizes:

1. **Differentiation from native LLM web search** — make it obvious that this tool
   does NOT call an LLM internally, does NOT just wrap a web search, and provides
   structured data (rules/templates/curated datasets) the LLM cannot replicate.
2. **Trigger clarity** — when should the calling agent invoke this tool vs. answer
   from its own knowledge? Lead with a one-sentence "Use this when ..." trigger.
3. **PlayMCP guideline compliance**:
   - English with the service name bilingual: "Hyodo Secretary(효도비서)" or
     "Gift Curator(선물고민러)" — keep this prefix.
   - Max 1024 chars (current ones are under 700 — you have headroom).
   - Must NOT contain the word "kakao" (case-insensitive, anywhere — prefix/suffix/
     middle all banned). Acceptable: "Korean messaging app", "KakaoTalk" is OK as a
     proper noun referring to the platform but PREFER "Korean messaging app" to be
     safe. Service names of partner MCPs ("SearchGift", "MemoChat") are fine.
   - No definitive claims like "guaranteed" / "100% accurate" — use "rule-based
     pattern matching" / "curated database" language instead.
4. **Routing precision in Kakao's GPT/Claude orchestrator** — when multiple Hyodo
   tools could apply (e.g. `check_suspicious_message` vs `compose_parent_warning`),
   the descriptions must make the sequential order obvious.

## Project context (for your judgment)

- **Hyodo Secretary(효도비서)**: KakaoTalk assistant helping adult children living
  apart from their elderly parents. Two flagship features: (1) generating greeting
  message context, (2) detecting scam messages parents forwarded to them.
- **Gift Curator(선물고민러)**: Gift recommendation assistant that filters out
  sponsored/ad-spam reviews from Naver/Tavily web search and surfaces only
  ad-free, repurchase-validated reviews. Integrates with the Korean messaging
  platform's first-party Gift MCP (SearchGift tool) by emitting compatible
  query/minPrice/maxPrice/customTags parameters.
- **All tools** are intentionally LLM-free internally — heavy reasoning is delegated
  to the calling agent (which is Kakao Tools' GPT-4o or Claude). Tools are pure
  data-retrieval / formatting / rule-matching. This is a hard contest constraint
  (100ms average latency target).
- The contest is the "Kakao AGENTIC PLAYER 10" — submission deadline 2026-07-14.

## Current tool descriptions to review

### Hyodo Secretary — 5 tools

**1. save_to_memo_chat** (current description, 380 chars):
```
Hyodo Secretary(효도비서). Format a Hyodo Secretary result (greeting message, scam warning, event reminder) into a clean text block ready for saving to the user's KakaoTalk MemoChat (나와의 채팅방). Returns the formatted text only. Does not call MemoChat MCP directly - the calling agent should pass this output to MemoChat MCP's MemoChat tool. Use this when the user explicitly wants to save a Hyodo Secretary result for later reference.
```

**2. compose_parent_warning** (current, 580 chars):
```
Hyodo Secretary(효도비서). Generate a parent-friendly warning message template about a detected scam, suitable for the user to forward to their parent. Returns structured templates (warning in elderly-friendly Korean, step-by-step action guide, suggested follow-up channels) tailored to the parent's age/profile. Does not call LLM internally - uses pre-curated elderly-friendly templates. Use this after check_suspicious_message returns a high-risk verdict and the user wants help warning their parent.
```

**3. compose_anbu** (current, 600 chars):
```
Hyodo Secretary(효도비서). Compose context data for a short greeting message to the user's parent based on parent profile, current season, weather, and recent news context. Returns structured data (parent profile breakdown, seasonal keywords, recommended tone, message templates) for the calling agent to synthesize the final greeting message in Korean. Does not call LLM internally - the calling agent (Kakao Tools GPT/Claude) handles the final message generation. Use this when the user wants to send a daily/weekly check-in message to their parent.
```

**4. find_upcoming_events** (current, 530 chars):
```
Hyodo Secretary(효도비서). Find upcoming events to check on the user's parent within a given time window. Combines seasonal events (Korean public holidays, seasonal health risks, climate transitions) with personal events extracted from parent_brief (birthdays, anniversaries, milestones). Returns structured event list with recommended check-in actions. Does not call LLM internally - uses static calendar data + simple text extraction. Use this when the user wants to plan parent care for the upcoming weeks.
```

**5. check_suspicious_message** (current, 680 chars):
```
Hyodo Secretary(효도비서). Analyze a Korean message (typed text, OCR result, or natural-language description) to detect scam/phishing/smishing patterns. Returns structured risk signals (suspicious URLs, suspicious keywords, matched scam types, recommended user actions) for the calling agent to make a final judgment and explain to the user. Does not call LLM internally - uses rule-based pattern matching against a curated database of Korean scam patterns. Use this when the user shares a suspicious KakaoTalk message (usually one their parent received).
```

### Gift Curator — 5 tools

**6. compose_gift_message** (current, 500 chars):
```
Gift Curator(선물고민러). Generate message card templates to accompany a gift, tailored to the relationship, occasion, and chosen gift. Returns 2-3 template variants in different tones (formal/casual/heartfelt) along with a tone selection guide. Does not call LLM internally - uses pre-curated Korean message templates organized by relationship type and occasion. Use this when the user has decided on a gift and needs help writing the accompanying message.
```

**7. find_real_recommendations** (current, 620 chars):
```
Gift Curator(선물고민러). Search external reviews for a specific keyword and return only non-ad sources. Applies F1 (explicit ad keyword matching: 협찬/체험단/공동구매/리뷰단/원고료/제공받은) and F2 (positive-signal scoring: 구매증빙·재구매·장기사용·단점언급 등 키워드 매칭) to surface trustworthy review excerpts. Returns up to N filtered sources with URL, excerpt, and ad-filter verification. Does not call LLM internally. Use this when the user explicitly wants to see 'real reviews' (광고 없는 진짜 후기) for a specific keyword without full curation.
```

**8. evaluate_gift_idea** (current, 570 chars):
```
Gift Curator(선물고민러). Evaluate a user-provided gift idea against the recipient context. Searches external reviews of the proposed item, filters out ads (F1 keyword filter), scores positive-signal categories (F2: purchase proof, third-party reaction, repurchase, etc.), and provides structured signals (review summary, category distribution, price context when budget given) for the calling agent to synthesize a final judgment. Does not call LLM internally. Use this when the user already has a gift candidate in mind and wants a second opinion.
```

**9. curate_gifts** (current, 730 chars):
```
Gift Curator(선물고민러). Generate curated gift candidates for the user's recipient based on relationship, occasion, budget, and recipient context. Combines Naver Blog/Cafe and Tavily web search results, filters out ads and sponsored content using rule-based detection (F1: 협찬/체험단/공동구매 keyword matching), scores positive signals (F2: 구매증빙/타인반응/재구매), and returns 3 candidates in distinct tones (practical / emotional / special). Each candidate includes SearchGift-compatible parameters (query, minPrice, maxPrice, customTags), non-ad source attribution, reasoning, and trend hints. Does not call LLM internally - the calling agent should pass each candidate's SearchGift params to the Kakao Gift MCP for catalog retrieval. Use this as the primary gift recommendation tool.
```

**10. refine_recommendation** (current, 660 chars):
```
Gift Curator(선물고민러). Generate new gift candidates based on user feedback on previous recommendations. Parses feedback signals (price too high/low, wrong category, wrong style) from a structured feedback_direction enum provided by the calling agent, then re-runs curation in that direction while avoiding the previous_keywords. Returns 3 new candidates in the same format as curate_gifts. Does not call LLM internally - the calling agent is responsible for parsing the user's free-form feedback into the structured feedback_direction input. Use this when the user reacts to a previous curate_gifts output with negative or directional feedback.
```

## Output format

Return ONE JSON object with this exact schema (no prose outside JSON):

{
  "review_summary": {
    "overall_assessment": "1-2 sentence verdict on the current set",
    "highest_risk_tool": "tool_name + why",
    "kakao_word_violations": ["list any tool that contains 'kakao' as a word — should be 0"]
  },
  "tools": {
    "save_to_memo_chat": {
      "current_char_count": 380,
      "suggested_description": "...your rewritten description here...",
      "suggested_char_count": 0,
      "changes_summary": ["3-bullet list of what changed and why"],
      "differentiation_score_1_to_5": 4,
      "trigger_clarity_score_1_to_5": 5,
      "risk_flags": []
    },
    ... (same shape for all 10 tools)
  },
  "global_recommendations": [
    "list of cross-cutting suggestions, e.g. consistent terminology, ordering hints between tools, etc."
  ]
}

Hard rules for `suggested_description`:
- Must start with "Hyodo Secretary(효도비서)." or "Gift Curator(선물고민러)."
- Must NOT contain the word "kakao" anywhere (case-insensitive). "KakaoTalk" is borderline — prefer "Korean messaging app" or just "messaging app". "Kakao Tools" → "the calling agent". "Kakao Gift MCP" → "the first-party Gift MCP".
- Must be under 1024 characters.
- Must NOT use definitive claims like "guaranteed", "100% accurate", "always".
- Lead with "Use this when ..." OR end with a clear "Use this when ..." trigger sentence.
- Make the LLM-free architecture point ONCE per description (not redundantly).
- For tools that DO call external web search (find_real_recommendations, evaluate_gift_idea, curate_gifts, refine_recommendation), state that explicitly so PlayMCP reviewers see the openWorldHint matches reality.

Return the JSON only. Begin now.
```

---

## 결과 받으면 본세션에서 할 일

1. JSON을 `docs/outsourcing/2026-06-26-task4-result.json`에 저장
2. `review_summary.kakao_word_violations`가 비어있는지 확인
3. 각 `suggested_description`을 Tool 파일 10개에 통합 (Edit 도구)
4. `tests/`에서 92/92 회귀 통과 확인
5. commit: `chore(descriptions): GPT-5 검수 반영 — Tool description 다듬기 (외주 #4)`
