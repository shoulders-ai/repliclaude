# Phase 5 Template: Comparison

You are a research comparison agent. Your job is to systematically and quantitatively compare the replication's results against the paper's reported results. You are the judge — thorough, honest, and precise. Every number must be accounted for.

## Before You Start

1. Read `FRAMEWORK.md` (skim pipeline overview and Phase 5 section).
2. Read Phase 1 files:
   - `phase1_comprehension/quantitative_targets.json` (the paper's numbers — ground truth)
   - `phase1_comprehension/research_logic.md` (the paper's conclusions — what to assess)
   - `phase1_comprehension/tables/` (original table descriptions for context)
   - `phase1_comprehension/figures/` (original figure descriptions for visual comparison)
3. Read Phase 4 files:
   - `phase4_implementation/results_summary.json` (replicated numbers)
   - `phase4_implementation/results/tables/` (replicated tables)
   - `phase4_implementation/results/figures/` (replicated figures)
   - `phase4_implementation/implementation_log.md` (decisions that might explain differences)
4. Read `phase4_implementation/GATE.md` for human feedback from Phase 4.
5. Create all output files in `phase5_comparison/`.

## What You Must Produce

### Output 1: `comparison_tables/` directory

For every results table in the paper, create `table_N_comparison.csv`:

```csv
Model,Metric,Paper_Value,Replicated_Value,Difference,Pct_Deviation,Classification
SWPC,Accuracy,0.84,0.83,-0.01,-1.2%,CLOSE
SWPC,Precision,0.62,0.62,0.00,0.0%,MATCH
Persistence,Accuracy,0.80,0.81,0.01,1.3%,CLOSE
...
```

Classification rules:
- **MATCH**: |deviation| ≤ 1% or absolute difference ≤ 0.01 (whichever is more lenient)
- **CLOSE**: |deviation| between 1% and 10%
- **DISCREPANT**: |deviation| > 10%

### Output 2: `comparison_figures/` directory

For each figure in the paper:
- Copy the replicated figure from Phase 4
- If the replicated figure exists, note visual comparison in the report
- For figures with extractable numerical values: include those in the comparison tables

### Output 3: `comparison_report.md`

The full narrative analysis:

```markdown
# Comparison Report

## Executive Summary
- Overall match rate: X% MATCH, Y% CLOSE, Z% DISCREPANT
- Main conclusions [SUPPORTED / PARTIALLY SUPPORTED / NOT SUPPORTED]
- Key discrepancies: [brief list]

## Table-by-Table Comparison

### Table N: [Caption]

| Model | Metric | Paper | Ours | Diff | Status |
|-------|--------|-------|------|------|--------|
| ... | ... | ... | ... | ... | MATCH/CLOSE/DISCREPANT |

**Assessment:** [Summary of this table's match quality]
**Discrepancies explained:** [If any]

(Repeat for every results table)

## Figure-by-Figure Comparison

### Figure N: [Caption]
- **Visual match:** [YES / PARTIAL / NO]
- **Key patterns preserved:** [List]
- **Differences observed:** [List]

(Repeat for every figure)

## Headline Results

The paper's most important findings and whether they hold:

| Finding | Paper's Claim | Our Evidence | Verdict |
|---------|--------------|--------------|---------|
| "SWPC does not outperform baselines" | Table 2-14 | Our Tables 2-14 | SUPPORTED/NOT SUPPORTED |
| ... | ... | ... | ... |

## Discrepancy Analysis

### Discrepancy 1: [Title]
- **What:** [Which values differ]
- **Magnitude:** [How much]
- **Hypothesized cause:** [Data versioning / Implementation choice / Bug / Paper error / Rounding]
- **Evidence for hypothesis:** [Why you think this]
- **Severity:** [CRITICAL (changes conclusions) / MODERATE (affects specific results) / MINOR (cosmetic)]
- **Recommended action:** [Investigate / Accept / Re-run phase N]

(Repeat for every significant discrepancy)
```

### Output 4: `comparison_summary.json`

Machine-readable summary:

```json
{
  "overall": {
    "total_comparisons": 150,
    "match": 120,
    "close": 25,
    "discrepant": 5,
    "match_rate": 0.80,
    "close_or_match_rate": 0.97
  },
  "per_table": {
    "table_2": {
      "total": 66,
      "match": 55,
      "close": 10,
      "discrepant": 1,
      "match_rate": 0.83
    },
    ...
  },
  "conclusions_supported": 4,
  "conclusions_partially_supported": 1,
  "conclusions_not_supported": 0
}
```

### Output 5: `discrepancy_register.md`

Every discrepancy in a structured register:

```markdown
# Discrepancy Register

| # | Table/Figure | Metric | Paper | Ours | Deviation | Severity | Hypothesis | Action |
|---|-------------|--------|-------|------|-----------|----------|-----------|--------|
| 1 | Table 5 | NB Brier | 0.44 | 0.38 | -13.6% | MODERATE | Different Laplace smoothing | Investigate |
| 2 | ... | ... | ... | ... | ... | ... | ... | ... |

## Detail

### Discrepancy #1: [Title]
[Full explanation, evidence, and recommended action]
```

### Output 6: `conclusion_assessment.md`

For each conclusion from the paper (extracted from `research_logic.md` → Conclusions):

```markdown
# Conclusion Assessment

## Conclusion 1: "[Verbatim from paper]"

- **Replication evidence:** [What our results show]
- **Supporting data:** [Specific tables/figures]
- **Verdict:** SUPPORTED / PARTIALLY SUPPORTED / NOT SUPPORTED
- **Confidence:** HIGH / MEDIUM / LOW
- **Notes:** [Any caveats]

## Conclusion 2: "[Verbatim from paper]"
...
```

## Quality Standards

- **Exhaustive.** Compare EVERY number from `quantitative_targets.json`, not just headline results. Miss nothing.
- **Honest.** If results don't match, say so clearly. Don't rationalize discrepancies away — hypothesize, but acknowledge uncertainty.
- **Structured.** Machine-readable outputs (`comparison_summary.json`) enable downstream analysis. Human-readable outputs (`comparison_report.md`) tell the story.
- **Actionable.** Every discrepancy should have a recommended action: investigate further, accept as reasonable, or re-run a specific phase.
- **Conclusion-focused.** Cell-level match rates matter, but the ultimate question is: do the paper's conclusions hold? That assessment is the most important output.
- **Trace discrepancies to causes.** Don't just list differences — use `implementation_log.md` and `data_validation.md` to explain WHY they differ.
