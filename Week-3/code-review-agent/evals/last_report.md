# Eval report — 2026-06-17 01:22 UTC

**FAIL** · recall 100% · precision 67% · F1 80% · 2.5 false positives/PR

- models: Qwen/Qwen3-235B-A22B-Instruct-2507, deepseek-ai/DeepSeek-V3.2, meta-llama/Llama-3.3-70B-Instruct, moonshotai/Kimi-K2.6
- judge: openai/gpt-oss-120b
- findings judged: valid=20 invalid=10 uncertain=0

## Thresholds
| metric | value | target | |
|---|---|---|---|
| recall | 100% | ≥80% | ✅ |
| precision | 67% | ≥70% | ❌ |
| FP/PR | 2.5 | ≤3.0 | ✅ |

## Recall by category
| category | caught / expected |
|---|---|
| quality | 4/4 |
| security | 2/2 |
| test_gap | 1/1 |

## Precision by agent (raw)
| agent | valid | invalid | uncertain | precision |
|---|---|---|---|---|
| quality | 12 | 7 | 0 | 63% |
| security | 7 | 1 | 0 | 88% |
| test_gap | 7 | 2 | 0 | 78% |

## False-positive taxonomy
| type | count |
|---|---|
| hallucinated | 4 |
| trivial | 4 |
| out_of_scope | 2 |

## Per-PR
| PR | findings | valid | invalid | recall | degraded |
|---|---|---|---|---|---|
| security-sql-injection | 10 | 8 | 2 | 2/2 | — |
| quality-refactor | 10 | 7 | 3 | 4/4 | — |
| test-gap | 10 | 5 | 5 | 1/1 | — |
| clean-feature-control | 0 | 0 | 0 | — (control) | — |

## Cost (tokens)
- agent tokens (this eval): 65288 (quality=51243, security=6824, test_gap=7221)
- judge tokens: 36702
