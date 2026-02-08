# repliclaude: User Manual

## What is this?

repliclaude is a framework for using AI (Claude Code) to autonomously replicate published scientific papers. You give it a PDF, it reads the paper, downloads the data, implements the methods, compares its results against the paper's results, and writes a report.

The point is not to produce perfect replications. The point is to explore: **how far can AI get on its own, and where does it break down?**

## Why this design?

This framework went through two major versions. v1 had 6 phases, 30+ output files, formal gate documents with checklists, and a 489-line Python tool for managing transitions. It worked mechanically but was overly formal and painful to use.

v2 stripped it down:

- **3 phases** (Understand, Replicate, Synthesize)
- **~12 output files** 
- **Conversational interaction** — the orchestrator talks to you in chat, you respond in chat. No mandatory file editing.
- **Comparison built into replication** — results are checked against the paper automatically as they're produced, not in a separate phase.
- **A running log** (`replicate/log.md`) that serves as audit trail, debug reference, AND raw material for the final report.

The core insight: the two things that actually matter are (1) deeply understanding the paper before writing any code, and (2) implementing the methods correctly with baselines-first validation. Everything else is either mechanical or assembly.

## The three phases

```
 PAPER (PDF)
     |
     v
 [1] UNDERSTAND --> brief.md + targets.json
     |               (what the paper does, every number to match)
     v  you confirm
 [2] REPLICATE  --> code + results + comparison.json + log.md
     |               (data, implementation, auto-comparison)
     v  you review verdict
 [3] SYNTHESIZE --> replication_report.md
                     (process, results, critique, proposed extensions)
```

**Your total involvement:** Depending on AI performance, interactions can be liomited to 2-3 chat messages per paper, while the AI does the rest.

---

## How to run a replication

### Prerequisites

- **Claude Code** (CLI) with Opus model
- This git repository cloned
- `.env` file in the project root with API keys:
  ```
  GEMINI_API_KEY=your_gemini_key
  ZAI_API_KEY=your_zai_key 
  ```
- Python venv set up: `python3 -m venv .venv && .venv/bin/pip install -r requirements.txt`

### Step 1: Add your paper

Drop a PDF into the project root. Name it `publication.pdf` (or any name — just reference it consistently).

### Step 2: Start a fresh Claude Code session

Open a new Claude Code session in this directory. The AI reads `FRAMEWORK.md` as its operating manual and the memory file (`.claude/`) for project context.

Say: **"Replicate this paper: publication.pdf"**

The orchestrator will automatically extract the PDF (sending it to Gemini), then launch the Phase 1 sub-agent. You don't need to run any commands manually.

### Step 3: Review the understanding

The AI will launch a sub-agent that reads the extraction and produces:
- `understand/brief.md` — structured understanding of the paper (metadata, methods, data sources, assumptions, reproducibility flags)
- `understand/targets.json` — every number from every results table (the machine-readable answer key)

The orchestrator will then print a summary in chat:
```
Paper: [title] by [authors]
Goal: [1 sentence]
Data: [sources]
Methods: [list]
Targets: 150 numbers across 14 tables
Assumptions: 3 identified

Proceed?
```

Review the summary. If something looks wrong, say so. If it looks fine, say **"proceed"** or **"run Phase 2"**.

### Step 4: Wait for replication

Phase 2 is the big one. The AI will:
1. Download all datasets
2. Validate data counts against the paper
3. Implement the simplest baseline model first (smoke test)
4. If the baseline matches: implement all remaining models
5. Auto-compare every result against `targets.json`
6. Log everything to `replicate/log.md`

**You don't need to do anything** unless the AI surfaces an issue:
- "Baseline accuracy is 0.65 but paper says 0.80 — should I investigate?"
- "Data source URL is down — do you have an alternative?"

When it's done, you'll see:
```
Replication complete.
Match rate: 87% MATCH, 10% CLOSE, 3% DISCREPANT
All 5 conclusions supported.

Ready for the report?
```

Say **"yes"** or **"run Phase 3"**.

### Step 5: Get the report

The AI writes `report/replication_report.md` — a concise, factual report covering:
1. What the paper does
2. What the replication did (narrative from the log)
3. Results comparison (key tables, verdict)
4. Assumptions made
5. Where the AI struggled
6. Paper review: strengths, concerns, proposed extensions

**This is your deliverable.** Edit it for voice and publish.

### Step 6: Check status anytime

```bash
bash tools/run.sh replic.py status
```

Output:
```
repliclaude Status
  understand    COMPLETE (2026-02-07)
  replicate     IN PROGRESS (3 checkpoints)
  report        PENDING
```

---

## Project structure

```
replicate-1/
  publication.pdf               # The paper to replicate
  .env                          # API keys (GEMINI_API_KEY, ZAI_API_KEY) — gitignored
  .venv/                        # Python virtual environment — gitignored

  FRAMEWORK.md                  # The orchestrator's operating manual (Claude reads this)
  USER_MANUAL.md                # This file (for humans)
  replic.py                     # Git checkpoint/tag/status tool (80 lines)
  requirements.txt              # Python dependencies

  templates/
    understand.md               # Sub-agent instructions for Phase 1
    replicate.md                # Sub-agent instructions for Phase 2
    synthesize.md               # Sub-agent instructions for Phase 3

  tools/
    extract_pdf.py              # PDF extraction (Gemini or Z.ai backends)
    run.sh                      # Python venv wrapper — always use this, never bare python3

  understand/                   # Phase 1 outputs
    extraction.md               # Raw Gemini extraction of the PDF
    brief.md                    # Structured paper understanding (created by Phase 1)
    targets.json                # Every number to reproduce (created by Phase 1)

  replicate/                    # Phase 2 outputs
    data/raw/                   # Downloaded raw data files
    data/processed/             # Analysis-ready datasets
    src/                        # Implementation code (metrics.py, model_*.py, run_all.py)
    results/tables/             # Replicated result tables as CSVs
    results/figures/            # Replicated figures as PNGs
    results.json                # Machine-readable replicated values
    comparison.json             # Auto-comparison: paper vs ours, per-cell classification
    log.md                      # Running narrative of everything that happened

  report/                       # Phase 3 output
    replication_report.md       # The final deliverable
```

## Key files explained

### `FRAMEWORK.md`
The AI's operating manual. When Claude Code starts a session in this directory, it reads this file to understand: what the project is, what the 3 phases are, what to do at each phase, how to interact with the human, when to pause for input, and how to use git. **You should never need to edit this file** unless you want to change the framework's behaviour.

### `templates/understand.md`
Detailed instructions for the Phase 1 sub-agent. Specifies exactly what `brief.md` and `targets.json` should contain, including format templates and quality rules. The orchestrator tells the sub-agent: "read this template and follow it." The human never interacts with this directly.

### `templates/replicate.md`
Instructions for the Phase 2 sub-agent. Specifies the 10-step process (setup → data → validation → metrics → baselines → models → results → comparison), the log format, when to stop and escalate, and quality rules. The critical rule: **baselines first, stop if >10% off.**

### `templates/synthesize.md`
Instructions for the Phase 3 sub-agent. Specifies the report structure (7 sections), writing standards (concise, factual, no AI voice), the 1,500-2,500 word target, and what makes Section 6 (Paper Review) the value-add.

### `tools/extract_pdf.py`
Unified PDF extraction with two backends:

```bash
# Default: Gemini 3 Flash — clean markdown, figure descriptions
bash tools/run.sh tools/extract_pdf.py paper.pdf output.md

# Higher quality: Gemini 3 Pro
bash tools/run.sh tools/extract_pdf.py paper.pdf output.md --model gemini-3-pro-preview

# High-fidelity OCR: Z.ai GLM-OCR — bounding boxes, raw JSON, best for scanned docs
bash tools/run.sh tools/extract_pdf.py paper.pdf output.md --backend zai
```

Gemini is the default because it produces cleaner, more structured output. Z.ai is available for when you need pixel-level accuracy or have a scanned/complex-layout PDF. The orchestrator can use Z.ai as a verification tool if something looks off in the Gemini extraction.

### `tools/run.sh`
A one-line wrapper that ensures Python runs inside the `.venv`. **Always use `bash tools/run.sh script.py` instead of `python3 script.py`.** This exists because on this machine, `python3` resolves to Python 3.14 (Homebrew) but `pip3` installs to Python 3.9. The venv isolates everything.

### `replic.py`
Lightweight git tool (80 lines). Three commands:
- `replic.py checkpoint "message"` — stages all changes and commits with a consistent `[replic]` prefix
- `replic.py tag <phase>` — marks a phase as complete (creates a git tag)
- `replic.py status` — shows which phases are done based on git tags

The orchestrator calls this at natural breakpoints. You never need to call it manually (but you can).

### `understand/targets.json`
The answer key. Every number the replication must reproduce, structured as JSON. The auto-comparison in Phase 2 loads this file and checks every replicated value against it. If a number isn't in targets.json, it won't be compared.

### `replicate/log.md`
The running narrative. The Phase 2 sub-agent appends to this as it works — data downloads, validation results, model outputs, decisions made, errors encountered. This serves three purposes:
1. **Audit trail** — what happened and why
2. **Report material** — Phase 3 pulls its narrative from this log
3. **Debug reference** — if something goes wrong, this shows where

### `replicate/comparison.json`
Auto-generated comparison of every replicated value against the paper. Each value is classified as MATCH (within 1%), CLOSE (1-10% off), or DISCREPANT (>10% off). Includes a summary with overall match rates and a per-conclusion assessment.

---

## Troubleshooting

### "The AI started doing something wrong"
Say **"stop"** in the chat. The orchestrator will halt. Explain what's wrong. It will course-correct or re-launch the sub-agent with new instructions. All previous work is preserved in git — nothing is lost.

### "I want to start over from scratch"
```bash
git log --oneline                    # Find the commit before things went wrong
git reset --hard <commit-hash>       # Reset to that point
bash tools/run.sh replic.py status   # Verify clean state
```

To reset the entire project to the framework-only state (no phase outputs):
```bash
git log --oneline                    # Find the framework commit
git reset --hard <framework-commit>  # Reset
rm -rf understand/brief.md understand/targets.json replicate/ report/
```

### "The Python environment is broken"
```bash
rm -rf .venv
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

### "The extraction looks wrong"
Re-run with a different backend or model:
```bash
# Try Gemini Pro instead of Flash
bash tools/run.sh tools/extract_pdf.py publication.pdf understand/extraction.md --model gemini-3-pro-preview

# Or try Z.ai for high-fidelity OCR
bash tools/run.sh tools/extract_pdf.py publication.pdf understand/extraction_zai.md --backend zai
```

### "I want to try a different paper"
The framework is paper-agnostic. To replicate a different paper:
1. Replace `publication.pdf` with your new paper
2. Re-run the extraction: `bash tools/run.sh tools/extract_pdf.py publication.pdf understand/extraction.md`
3. Start a fresh Claude Code session
4. Say "Run Phase 1"

### "The AI's context is getting full"
Claude Code sessions have finite context. If the context fills up during Phase 2 (the longest phase), the session will compress earlier messages. This is fine — all work is saved to files and git. If a session ends entirely, start a new one and say "Continue from where the previous session left off — check `replic.py status` and the existing output files."

---

## Choosing a good paper

Best candidates:
- **Public data** — no authentication, no restricted access
- **Standard methods** — regression, classification, standard statistical tests. Not custom simulations or proprietary models.
- **Quantitative results** — tables of numbers that can be compared. Not qualitative or purely visual results.
- **Clear methodology** — enough detail to re-implement without guessing
- **Moderate size** — 5-20 pages, 3-15 results tables. Not a 60-page methods paper.

## What to expect

- **80-95% of numbers will match.** Perfect replication is rare even for humans.
- **Data acquisition is the most fragile step.** URLs break, formats change, catalogs get updated between the paper's version and yours.
- **The AI will make assumptions.** Papers rarely specify every implementation detail. The AI documents its assumptions and you can override them.
- **Phase 2 takes the longest.** Expect 15-45 minutes depending on paper complexity.
- **The report needs your editing.** The AI writes a solid draft. You add voice, context, and narrative.

---

## Current test paper

The project is currently set up with: **Camporeale & Berger (2025) "Verification of the NOAA SWPC Solar Flare Forecast (1998-2024)"** from Space Weather journal. This paper evaluates NOAA's solar flare forecasts over 26 years against zero-cost baselines (persistence, climatology, Naive Bayes, logistic regression). Key finding: SWPC doesn't outperform simple baselines.

The Gemini extraction is already done (`understand/extraction.md`, 63K chars). The project is ready for Phase 1.
