# REPLIC-AI v2

A framework for using AI to replicate published scientific papers. Three phases, minimal ceremony, conversational interaction.

---

## How It Works

```
 PAPER (PDF)
     │
     ▼
 [1] UNDERSTAND ──→ brief.md + targets.json
     │                (what the paper does, every number to match)
     ▼  human confirms
 [2] REPLICATE ───→ code + results + comparison.json + log.md
     │                (data, implementation, auto-comparison)
     ▼  human reviews verdict
 [3] SYNTHESIZE ──→ replication_report.md
                      (process, results, critique, proposed extensions)
```

Total human touchpoints: 2-3 for a simple paper, 4+ for a complex one.

---

## Roles

**Orchestrator** (Claude Code Opus 4.5, this session):
- Reads this document as its operating manual
- Launches sub-agents via Task tool: "read `templates/X.md`, then do the work"
- Surfaces key findings in chat — the human responds in chat, not by editing files
- Calls `replic.py` for git checkpoints and tags
- Decides when to pause for human input vs. continue silently

**Sub-agents** (launched via Task tool):
- Read their template from disk
- Write output files
- Never manage transitions or interact with the human

**Human**:
- Drops a PDF and says "replicate this"
- Responds to orchestrator questions in chat
- Reviews the final report
- Edits and publishes

---

## Phase 1: UNDERSTAND

**What happens:** Sub-agent reads the Gemini-extracted PDF content and produces a structured understanding of the paper.

**Inputs:**
- `understand/extraction.md` (produced by `tools/extract_pdf_gemini.py` before this phase)
- The original PDF (for visual verification of figures/tables if needed)

**Outputs:**
- `understand/brief.md` — single file containing: metadata, research logic chain (context → questions → methods → data → results → conclusions), data sources with URLs, assumptions with defaults, reproducibility flags. This replaces 5 separate v1 files.
- `understand/targets.json` — every number from every results table, plus descriptive statistics and key numbers from running text. The machine-readable answer key.

**Sub-agent template:** `templates/understand.md`

**Orchestrator prompt:**
```
Read templates/understand.md for your instructions.
Read FRAMEWORK.md for overall context (skim).
Read understand/extraction.md — this is the paper content.
Write outputs to understand/.
```

**Human touchpoint:** After the sub-agent finishes, the orchestrator prints a summary in chat:
```
Paper: [title] by [authors]
Goal: [1 sentence]
Data: [sources with availability]
Methods: [list]
Targets: [count] numbers to reproduce across [count] tables
Assumptions: [count] — [list the important ones with defaults]
Risks: [any blockers]

Proceed? Any scope changes?
```

The human responds conversationally. No file editing. The orchestrator captures any corrections by updating the output files directly.

**Git:** `replic.py checkpoint "understand: extraction and brief"` then `replic.py tag understand`

---

## Phase 2: REPLICATE

**What happens:** Sub-agent acquires data, implements all methods, runs them, and auto-compares results against `targets.json`. Everything is logged to `log.md` as it happens.

**Inputs:**
- `understand/brief.md` (what to implement)
- `understand/targets.json` (what to match)

**Outputs:**
- `replicate/data/raw/` — downloaded raw files
- `replicate/data/processed/` — analysis-ready datasets
- `replicate/src/` — all implementation code (metrics.py, model_*.py, run_all.py)
- `replicate/results/tables/` — replicated result tables as CSVs
- `replicate/results/figures/` — replicated figures as PNGs
- `replicate/results.json` — machine-readable results
- `replicate/comparison.json` — auto-generated per-cell comparison (paper vs ours, MATCH/CLOSE/DISCREPANT)
- `replicate/log.md` — running narrative of everything that happened

**Sub-agent template:** `templates/replicate.md`

**Orchestrator prompt:**
```
Read templates/replicate.md for your instructions.
Read FRAMEWORK.md for overall context (skim).
Read understand/brief.md — this is what you need to implement.
Read understand/targets.json — these are the numbers to match.
Write all outputs to replicate/.
Use bash tools/run.sh for all Python execution.
```

**Execution order (enforced by template):**
1. Set up environment, install packages
2. Download and parse data
3. Validate data counts against targets.json → log results
4. Implement metrics module with unit tests
5. Implement simplest baseline → compare against paper → if >10% off, STOP and return to orchestrator
6. Implement remaining models
7. Generate all results tables and figures
8. Run auto-comparison against targets.json → write comparison.json
9. Log everything to log.md

**Human touchpoints during Phase 2:**
The orchestrator interrupts the human ONLY when:
- A baseline diverges >10% from paper values
- A data source is unavailable with no fallback
- An ambiguity arises not covered by brief.md assumptions
- Code fails after 3 attempts on the same error

On the happy path, the orchestrator stays silent until Phase 2 completes, then surfaces:
```
Replication complete.
Match rate: X% MATCH, Y% CLOSE, Z% DISCREPANT
Conclusions: [N/N] supported
Notable discrepancies: [list if any]

Ready for the report?
```

**Git:** Multiple checkpoints during Phase 2:
```
replic.py checkpoint "replicate: data acquired and validated"
replic.py checkpoint "replicate: baselines verified"
replic.py checkpoint "replicate: all models complete"
replic.py tag replicate
```

---

## Phase 3: SYNTHESIZE

**What happens:** Sub-agent reads everything and writes the final report. No code execution.

**Inputs:**
- `understand/brief.md`
- `understand/targets.json`
- `replicate/log.md`
- `replicate/comparison.json`
- `replicate/results.json`

**Output:**
- `report/replication_report.md` — the deliverable

**Sub-agent template:** `templates/synthesize.md`

**Orchestrator prompt:**
```
Read templates/synthesize.md for your instructions.
Read FRAMEWORK.md for overall context (skim).
Read ALL files listed in the template's "Inputs" section.
Write the report to report/replication_report.md.
```

**Human touchpoint:** Human reads the report, edits for voice, publishes.

**Git:** `replic.py checkpoint "report: replication report"` then `replic.py tag report`

---

## Adaptive Complexity

After Phase 1, the orchestrator classifies the paper:

| Tier | Criteria | Behavior |
|------|----------|----------|
| **Simple** | 1 dataset, standard methods, <5 results tables | Phase 2 runs straight through. 2 human touchpoints total. |
| **Standard** | Multiple datasets or methods, 5-15 tables | Phase 2 pauses after baselines for sanity check. 3 touchpoints. |
| **Complex** | Novel methods, ambiguous methodology, many tables, multiple data sources | Phase 2 may use multiple sub-agent launches. Pauses after each major model group. 4+ touchpoints. |

The tier is determined by: number of data sources, number of methods, number of results tables, count of reproducibility flags, and any LOW confidence ratings in brief.md.

The orchestrator announces the tier to the human after Phase 1: "This is a [simple/standard/complex] replication."

---

## The Log

`replicate/log.md` is the key artifact. It accumulates as the sub-agent works:

```markdown
## 14:23 — Data Download
Downloaded SWPC forecasts (29 files, 2.3MB). All URLs 200.

## 14:31 — Data Validation
| Metric | Paper | Ours | Status |
|--------|-------|------|--------|
| Total days | 9828 | 9828 | MATCH |
| X-class positive | 254 | 252 | CLOSE |

X-class off by 2. Catalog version difference (ASR v1.0.0 vs paper's version). Proceeding.

## 14:45 — Baseline: Persistence
Accuracy: paper=0.80, ours=0.80. MATCH. Pipeline validated.
```

Three purposes:
1. **Audit trail** — what happened, when, what decisions were made
2. **Report raw material** — Phase 3 pulls the narrative from this log
3. **Debug reference** — if something goes wrong later, the log shows where

---

## Auto-Comparison

Comparison is not a separate phase. It's built into `run_all.py`:

1. Load `targets.json`
2. After each model runs, compare every metric against paper values
3. Classify: **MATCH** (≤1%), **CLOSE** (1-10%), **DISCREPANT** (>10%)
4. Write `comparison.json` with per-cell results
5. Log summary to `log.md`

The sub-agent sees discrepancies immediately and can investigate in the same session.

---

## Git Workflow

`replic.py` provides three commands:

```bash
replic.py checkpoint "message"   # git add -A + commit with consistent format
replic.py tag <phase>            # git tag marking phase completion
replic.py status                 # show which phases are complete
```

The orchestrator calls these at natural breakpoints. The human never touches git.

`replic.py status` output:
```
REPLIC-AI Status
  understand    COMPLETE (2026-01-30)
  replicate     IN PROGRESS (3 checkpoints)
  report        PENDING
```

---

## Go-Back

No formal mechanism. Just:
1. Fix the upstream file (e.g., correct a value in targets.json)
2. `replic.py checkpoint "fix: corrected Table 5 values"`
3. Re-run the affected work
4. The log captures what happened

---

## Tooling

- **Language:** Python. All code in `.venv`. Use `bash tools/run.sh script.py` — never bare `python3` or `pip3`.
- **PDF extraction:** `tools/extract_pdf_gemini.py` — sends PDF to Gemini, returns structured markdown.
- **Git:** `replic.py` — lightweight checkpoint/tag/status tool.

---

## What Makes a Paper Good for This

- **Public data** — no proprietary or access-restricted datasets
- **Standard methods** — well-known algorithms, not bespoke simulations
- **Quantitative results** — tables of numbers, not qualitative findings
- **Moderate complexity** — complex enough to be interesting, not so complex it requires months of domain expertise

---

## Honest Expectations

This framework will not produce perfect replications. Expected failure modes:

- **Data acquisition** is the most fragile step. URLs break, formats change, catalogs get updated.
- **Ambiguous methodology** forces assumptions. Different assumptions → different results.
- **Domain knowledge gaps** mean the AI may misunderstand subtle methodological choices.
- **Numerical precision** — expect 80-95% of values to match, not 100%.

The point is not perfection. The point is: how far can AI get, and where does it break down?
