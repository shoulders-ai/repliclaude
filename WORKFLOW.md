# REPLIC-AI: Workflow Guide

How the human, the orchestrator (Claude Code Opus), and sub-agents interact in practice.

---

## Roles

| Role | Who | Does what |
|------|-----|-----------|
| **Human** | You | Says "run phase N", reviews GATE.md, says "proceed" or "redo", edits nothing except adding notes below the marked line in GATE.md |
| **Orchestrator** | Claude Code (Opus 4.5, this session) | Reads FRAMEWORK.md as its operating manual. Manages phase transitions. Launches sub-agents. Writes GATE.md. Calls phase_gate.py. |
| **Sub-agent** | Launched via Task tool | Reads its phase template + FRAMEWORK.md. Does the actual work. Writes output files. Returns summary to orchestrator. Never calls phase_gate.py. |

---

## The Phase Lifecycle

Each phase goes through three transitions:

```
START ──→ [sub-agent works] ──→ COMMIT ──→ [human reviews] ──→ COMPLETE
```

| Transition | What happens | Who triggers |
|------------|-------------|--------------|
| `start N` | Validates upstream phases are complete and unchanged. Creates phase directory. Logs "STARTED" to ledger. | Orchestrator |
| `commit N` | Git commits all sub-agent outputs + GATE.md. Records file hashes. Logs "COMMITTED". This is the sub-agent's frozen snapshot. | Orchestrator |
| `complete N` | Git commits any human additions to GATE.md. Snapshots conversation. Locks the phase. Downstream phases can now start. Logs "COMPLETED". | Orchestrator (after human says "proceed") |

---

## What Actually Happens: Step by Step

### Human says: "run phase 1"

```
┌─────────────────────────────────────────────────────────┐
│ ORCHESTRATOR                                            │
│                                                         │
│  1. Runs: python phase_gate.py start 1                  │
│     → Validates no upstream dependencies (phase 1 has   │
│       none). Creates phase1_comprehension/ directory.   │
│     → STATUS.md updated: Phase 1 = IN PROGRESS          │
│     → LEDGER.md appended: "Phase 1 STARTED"             │
│                                                         │
│  2. Launches sub-agent via Task tool:                   │
│     Prompt: "Before doing anything, read these files:   │
│       - templates/phase1.md (your detailed instructions)│
│       - FRAMEWORK.md (overall context — skim)           │
│     Then read publication.pdf and execute the template  │
│     instructions. Write all outputs to                  │
│     phase1_comprehension/"                              │
│                                                         │
│  3. Sub-agent works... reads PDF, extracts tables,      │
│     builds logic chain, writes all output files.        │
│     Returns summary to orchestrator.                    │
│                                                         │
│  4. Orchestrator reviews sub-agent summary.             │
│     Writes phase1_comprehension/GATE.md with:           │
│       - Summary of what was produced                    │
│       - Confidence assessment                           │
│       - Items requiring human verification              │
│       - Checklist with checkboxes                       │
│       - "Human Notes" section (empty, for human)        │
│                                                         │
│  5. Runs: python phase_gate.py commit 1                 │
│     → Git commits all sub-agent outputs + GATE.md       │
│     → File hashes recorded                              │
│     → LEDGER.md appended: "Phase 1 COMMITTED"           │
│                                                         │
│  6. Says to human: "Phase 1 complete. Please review     │
│     phase1_comprehension/GATE.md and let me know:       │
│     'proceed' or 'redo'."                               │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### Human reviews GATE.md

The human opens `phase1_comprehension/GATE.md` in their editor. They see:

```markdown
# Phase 1 Gate: Comprehension

## Sub-agent Summary
Extracted 14 tables, 6 figures, full research logic chain, and
quantitative targets from Camporeale & Berger (2025).

## Confidence Assessment
- Metadata: HIGH
- Tables: HIGH (14/14 extracted as CSVs)
- Research logic chain: MEDIUM (see flags)
- Quantitative targets: HIGH
- Reproducibility flags: 3 items identified

## Items Requiring Human Verification
1. [p.7] Buffer period described as "1996-2008 to 1997-2012" —
   interpreted as Aug 1996 to Dec 1997. Is this correct?
2. Sunspot number source not specified in paper. Needed for
   baseline models in Phase 3.
3. [p.9] Typo correction "71/71/71 → 70/70/70" is a domain-
   specific judgment the AI would not independently make.

## Checklist
- [ ] Tables correctly extracted
- [ ] Research logic chain accurate
- [ ] All data sources identified
- [ ] Quantitative targets complete
- [ ] APPROVED TO PROCEED

---
## Human Notes
(add your notes below this line — do not edit above)

```

The human:
- Checks the boxes
- Writes notes below the line, e.g.: "Sunspot data confirmed as SILSO. Buffer period interpretation is correct."
- Saves the file

### Human says: "proceed"

```
┌─────────────────────────────────────────────────────────┐
│ ORCHESTRATOR                                            │
│                                                         │
│  1. Re-reads phase1_comprehension/GATE.md               │
│     → Sees human notes and checked boxes                │
│                                                         │
│  2. Runs: python phase_gate.py complete 1               │
│     → Git commits human's GATE.md additions             │
│     → Snapshots full conversation log                   │
│     → Locks phase (MANIFEST.json with hashes)           │
│     → STATUS.md updated: Phase 1 = COMPLETE             │
│     → LEDGER.md appended: "Phase 1 COMPLETED"           │
│                                                         │
│  3. Says: "Phase 1 locked. Ready for phase 2?"          │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### Alternative: Human says "redo"

```
┌─────────────────────────────────────────────────────────┐
│ ORCHESTRATOR                                            │
│                                                         │
│  1. Reads human feedback (from chat or GATE.md notes)   │
│                                                         │
│  2. Decides: re-run sub-agent with revised instructions │
│     OR do targeted fix itself                           │
│                                                         │
│  3. If re-running sub-agent:                            │
│     → Launches new sub-agent with additional guidance:  │
│       "Read templates/phase1.md. Also read GATE.md for  │
│        human feedback on the previous attempt. Focus    │
│        on fixing: [specific issue]."                    │
│     → Sub-agent overwrites output files                 │
│     → Orchestrator writes updated GATE.md               │
│     → Runs: python phase_gate.py commit 1               │
│       (new commit — old attempt preserved in git)       │
│     → Back to human review                              │
│                                                         │
│  4. If doing targeted fix:                              │
│     → Orchestrator edits specific files directly        │
│     → Updates GATE.md                                   │
│     → Runs: python phase_gate.py commit 1               │
│     → Back to human review                              │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## Phase Transitions: What Gets Committed When

```
git log for a typical phase:

  commit abc123 — "phase 1: start"
    STATUS.md, LEDGER.md

  commit def456 — "phase 1: commit (attempt 1)"
    phase1_comprehension/replication_brief.md
    phase1_comprehension/research_logic.md
    phase1_comprehension/tables/*.csv
    phase1_comprehension/figures/*.png
    phase1_comprehension/quantitative_targets.json
    phase1_comprehension/GATE.md
    phase1_comprehension/MANIFEST.json

  commit 789abc — "phase 1: complete"
    phase1_comprehension/GATE.md  (human additions)
    phase1_comprehension/conversation_log.md
    phase1_comprehension/MANIFEST.json  (final hashes)
    LEDGER.md
    STATUS.md
```

If the human says "redo", there's an extra commit between commit and complete:

```
  commit def456 — "phase 1: commit (attempt 1)"
  commit aaa111 — "phase 1: commit (attempt 2, addressing human feedback)"
  commit 789abc — "phase 1: complete"
```

Git history preserves every attempt.

---

## Rules

1. **The human never calls phase_gate.py directly.** The orchestrator handles all transitions.
2. **The human never edits sub-agent outputs.** They only add notes below the marked line in GATE.md. If something needs changing, they say "redo" and the orchestrator handles it.
3. **Sub-agents never call phase_gate.py.** They just read their template and write output files.
4. **Every sub-agent attempt is committed** before human review. Nothing is lost.
5. **Phases must complete sequentially.** Phase N+1 cannot start until Phase N is complete. If Phase N outputs are modified after completion, downstream phases are flagged as stale.
6. **The conversation log is captured** at phase completion, creating an audit trail that survives session compaction.
