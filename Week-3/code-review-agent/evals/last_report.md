# Eval report — 2026-06-17 01:56 UTC

**PASS** · recall 100% · precision 85% · F1 92% · 1.2 false positives/PR

- models: Qwen/Qwen3-235B-A22B-Instruct-2507, deepseek-ai/DeepSeek-V3.2, meta-llama/Llama-3.3-70B-Instruct, moonshotai/Kimi-K2.6
- judge: openai/gpt-oss-120b
- findings judged: valid=28 invalid=5 uncertain=0

## Thresholds
| metric | value | target | |
|---|---|---|---|
| recall | 100% | ≥80% | ✅ |
| precision | 85% | ≥70% | ✅ |
| FP/PR | 1.2 | ≤3.0 | ✅ |

## Recall by category
| category | caught / expected |
|---|---|
| quality | 4/4 |
| security | 2/2 |
| test_gap | 1/1 |

## Precision by agent (raw)
| agent | valid | invalid | uncertain | precision |
|---|---|---|---|---|
| quality | 20 | 5 | 0 | 80% |
| security | 13 | 0 | 0 | 100% |
| test_gap | 9 | 0 | 0 | 100% |

## False-positive taxonomy
| type | count |
|---|---|
| out_of_scope | 3 |
| trivial | 1 |
| misread | 1 |

## Per-PR
| PR | findings | valid | invalid | recall | degraded |
|---|---|---|---|---|---|
| security-sql-injection | 12 | 10 | 2 | 2/2 | — |
| quality-refactor | 8 | 8 | 0 | 4/4 | — |
| test-gap | 13 | 10 | 3 | 1/1 | — |
| clean-feature-control | 0 | 0 | 0 | — (control) | — |

## Cost (tokens)
- agent tokens (this eval): 132344 (quality=100622, security=15400, test_gap=16322)
- judge tokens: 42963
