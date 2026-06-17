# Eval report — 2026-06-17 10:39 UTC

**PASS** · recall 88% · precision 86% · F1 87% · 0.4 false positives/PR

- models: Qwen/Qwen3-235B-A22B-Instruct-2507, deepseek-ai/DeepSeek-V3.2, meta-llama/Llama-3.3-70B-Instruct, moonshotai/Kimi-K2.6
- judge: openai/gpt-oss-120b
- findings judged: valid=19 invalid=3 uncertain=0

## Thresholds
| metric | value | target | |
|---|---|---|---|
| recall | 88% | ≥80% | ✅ |
| precision | 86% | ≥70% | ✅ |
| FP/PR | 0.4 | ≤3.0 | ✅ |

## Recall by category
| category | caught / expected |
|---|---|
| quality | 4/5 |
| security | 2/2 |
| test_gap | 1/1 |

## Precision by agent (raw)
| agent | valid | invalid | uncertain | precision |
|---|---|---|---|---|
| quality | 14 | 2 | 0 | 88% |
| security | 7 | 1 | 0 | 88% |
| test_gap | 8 | 1 | 0 | 89% |

## False-positive taxonomy
| type | count |
|---|---|
| out_of_scope | 2 |
| trivial | 1 |

## Per-PR
| PR | findings | valid | invalid | recall | degraded |
|---|---|---|---|---|---|
| security-sql-injection | 7 | 5 | 2 | 2/2 | — |
| quality-refactor | 6 | 6 | 0 | 3/4 | — |
| test-gap | 5 | 5 | 0 | 1/1 | — |
| breaking-signature-callers | 1 | 1 | 0 | 1/1 | — |
| clean-feature-control | 0 | 0 | 0 | — (precision only) | — |
| real-click-3578 | 1 | 1 | 0 | — (precision only) | — |
| real-click-3534 | 0 | 0 | 0 | — (precision only) | — |
| real-requests-7502 | 2 | 1 | 1 | — (precision only) | — |

## Cost (tokens)
- agent tokens (this eval): 108015 (quality=78740, security=14732, test_gap=14543)
- judge tokens: 28980
