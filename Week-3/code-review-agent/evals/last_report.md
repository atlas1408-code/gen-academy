# Eval report — 2026-06-17 01:41 UTC

**PASS** · recall 100% · precision 84% · F1 91% · 1.0 false positives/PR

- models: Qwen/Qwen3-235B-A22B-Instruct-2507, deepseek-ai/DeepSeek-V3.2, meta-llama/Llama-3.3-70B-Instruct, moonshotai/Kimi-K2.6
- judge: openai/gpt-oss-120b
- findings judged: valid=21 invalid=4 uncertain=0

## Thresholds
| metric | value | target | |
|---|---|---|---|
| recall | 100% | ≥80% | ✅ |
| precision | 84% | ≥70% | ✅ |
| FP/PR | 1.0 | ≤3.0 | ✅ |

## Recall by category
| category | caught / expected |
|---|---|
| quality | 4/4 |
| security | 2/2 |
| test_gap | 1/1 |

## Precision by agent (raw)
| agent | valid | invalid | uncertain | precision |
|---|---|---|---|---|
| quality | 15 | 4 | 0 | 79% |
| security | 6 | 0 | 0 | 100% |
| test_gap | 5 | 0 | 0 | 100% |

## False-positive taxonomy
| type | count |
|---|---|
| out_of_scope | 2 |
| trivial | 2 |

## Per-PR
| PR | findings | valid | invalid | recall | degraded |
|---|---|---|---|---|---|
| security-sql-injection | 9 | 7 | 2 | 2/2 | — |
| quality-refactor | 8 | 8 | 0 | 4/4 | — |
| test-gap | 8 | 6 | 2 | 1/1 | — |
| clean-feature-control | 0 | 0 | 0 | — (control) | — |

## Cost (tokens)
- agent tokens (this eval): 97383 (quality=74504, security=10828, test_gap=12051)
- judge tokens: 32398
