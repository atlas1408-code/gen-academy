# Eval report — 2026-06-17 03:09 UTC

**PASS** · recall 100% · precision 79% · F1 88% · 1.8 false positives/PR

- models: Qwen/Qwen3-235B-A22B-Instruct-2507, deepseek-ai/DeepSeek-V3.2, meta-llama/Llama-3.3-70B-Instruct, moonshotai/Kimi-K2.6
- judge: openai/gpt-oss-120b
- findings judged: valid=34 invalid=9 uncertain=0

## Thresholds
| metric | value | target | |
|---|---|---|---|
| recall | 100% | ≥80% | ✅ |
| precision | 79% | ≥70% | ✅ |
| FP/PR | 1.8 | ≤3.0 | ✅ |

## Recall by category
| category | caught / expected |
|---|---|
| quality | 5/5 |
| security | 2/2 |
| test_gap | 1/1 |

## Precision by agent (raw)
| agent | valid | invalid | uncertain | precision |
|---|---|---|---|---|
| quality | 26 | 8 | 0 | 76% |
| security | 16 | 0 | 0 | 100% |
| test_gap | 12 | 1 | 0 | 92% |

## False-positive taxonomy
| type | count |
|---|---|
| out_of_scope | 4 |
| misread | 3 |
| trivial | 2 |

## Per-PR
| PR | findings | valid | invalid | recall | degraded |
|---|---|---|---|---|---|
| security-sql-injection | 13 | 10 | 3 | 2/2 | — |
| quality-refactor | 12 | 12 | 0 | 4/4 | — |
| test-gap | 16 | 11 | 5 | 1/1 | — |
| breaking-signature-callers | 1 | 1 | 0 | 1/1 | — |
| clean-feature-control | 1 | 0 | 1 | — (control) | — |

## Cost (tokens)
- agent tokens (this eval): 313737 (quality=234587, security=39761, test_gap=39389)
- judge tokens: 60036
