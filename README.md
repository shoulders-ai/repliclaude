# repliclaude

An experiment in AI-driven scientific replication. Claude Code was given a published paper and asked to independently replicate its analysis — downloading data, implementing methods, and comparing results — with minimal human intervention.

## The Paper

**Camporeale & Berger (2025).** *Verification of the NOAA Space Weather Prediction Center Solar Flare Forecast (1998–2024).* Space Weather, 23(10).
[Read the paper](https://agupubs.onlinelibrary.wiley.com/doi/full/10.1029/2025SW004546) ·  PDF also included as [`publication.pdf`](publication.pdf)

NOAA's Space Weather Prediction Center (SWPC) issues daily probabilistic forecasts for solar flares — events that can endanger astronauts and damage satellites. This paper asked a simple, devastating question: **are those forecasts actually any good?** The authors evaluated 26 years of SWPC M-class and X-class flare forecasts (9,828 days) against zero-cost baselines — persistence (yesterday's outcome), climatology (historical averages), Naive Bayes, and logistic regression. The conclusion: SWPC forecasts do not outperform these trivial methods on the metrics that matter most, and are dangerously miscalibrated for X-class events.

## What Happened Here

Claude Code ran a 3-phase pipeline: **Understand** (extract and analyze the paper) → **Replicate** (download data, implement all models, compare results) → assess. The entire replication was done in a single Claude Code session with light human oversight. The conversation transcript is included.

**Bottom line:** 5 models implemented, 297 numerical values compared against the paper. Persistence matched perfectly (66/66). SWPC evaluation matched 95% (63/66). Climatology, Naive Bayes, and Logistic Regression had lower match rates due to ambiguities in the paper's feature computation — but all 5 of the paper's conclusions were independently confirmed.

| Model | Match | Close | Discrepant |
|-------|-------|-------|------------|
| Persistence | 66/66 (100%) | — | — |
| SWPC | 63/66 (95%) | 3 | — |
| Climatology | lower | — | feature spec ambiguity |
| Naive Bayes | lower | — | unspecified model details |
| Logistic Reg. | lower | — | same feature issue |
| **Total** | **156/297 (53%)** | **35 (12%)** | **106 (36%)** |

All 5 paper conclusions **supported**: SWPC doesn't beat baselines on event-sensitive metrics; accuracy/Brier scores are misleading due to class imbalance; X-class forecasts are severely miscalibrated; "storm after the calm" detection fails; "all-clear" periods are poorly identified.

## Repository Map

```
.
├── README.md                  ← you are here
├── publication.pdf            ← the original paper
│
├── understand/                ← Phase 1: paper analysis
│   ├── extraction.md          ← full text extracted from PDF via Gemini
│   ├── brief.md               ← structured replication brief (data sources, methods, targets)
│   └── targets.json           ← 297 specific numerical targets to reproduce
│
├── replicate/                 ← Phase 2: implementation & results
│   ├── src/                   ← all replication code
│   │   ├── download_data.py   ← data acquisition from NOAA/SWPC/SILSO
│   │   ├── parse_data.py      ← data parsing and evaluation dataset construction
│   │   ├── metrics.py         ← verification metrics (Brier, AUC, TSS, HSS, etc.)
│   │   ├── test_metrics.py    ← unit tests for metrics (19 tests, all passing)
│   │   ├── model_*.py         ← one file per model (persistence, climatology, swpc, etc.)
│   │   └── run_all.py         ← orchestrator that runs all models and compares to paper
│   ├── data/                  ← raw + processed datasets (~120 MB)
│   ├── results/tables/        ← replicated Tables 2–7 as CSV
│   ├── results.json           ← all numerical results in machine-readable format
│   ├── comparison.json        ← automated comparison against paper (MATCH/CLOSE/DISCREPANT)
│   └── log.md                 ← narrative log of the replication process
│
├── logs/                      ← Claude Code conversation transcript
│   └── session-replicate.jsonl ← raw session log from the replication phase
│
├── FRAMEWORK.md               ← the repliclaude operating manual (3-phase pipeline)
├── USER_MANUAL.md             ← how to use this framework on other papers
├── templates/                 ← prompt templates for each pipeline phase
├── tools/                     ← PDF extraction, venv wrapper
├── replic.py                  ← git checkpoint utility used during the run
└── CLAUDE.md                  ← project context for Claude Code sessions
```

## Key Artifacts

| If you want to... | Go to |
|---|---|
| Read the paper | [`publication.pdf`](publication.pdf) or [online](https://agupubs.onlinelibrary.wiley.com/doi/full/10.1029/2025SW004546) |
| See what the AI understood | [`understand/brief.md`](understand/brief.md) |
| See the replication code | [`replicate/src/`](replicate/src/) |
| See the results | [`replicate/results.json`](replicate/results.json) |
| See how results compare to paper | [`replicate/comparison.json`](replicate/comparison.json) |
| Read the narrative log | [`replicate/log.md`](replicate/log.md) |
| Read the AI conversation | [`logs/session-replicate.jsonl`](logs/session-replicate.jsonl) |
| Understand the framework | [`FRAMEWORK.md`](FRAMEWORK.md) |

## How It Was Built

This is a [Claude Code](https://docs.anthropic.com/en/docs/claude-code) project. The replication was performed by Claude (Opus) running autonomously inside the CLI, with the human operator providing high-level direction ("go", "run all models", etc.) rather than writing code. The full conversation transcript is in [`logs/`](logs/).

The framework (`FRAMEWORK.md`, `templates/`, `tools/`) is designed to be reusable for other papers.
