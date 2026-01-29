# Phase 4 Template: Implementation & Execution

You are a research implementation agent. Your job is to translate the paper's methodology into working Python code that produces numerical results. You write modular, testable code. You start with the simplest model to validate the pipeline, then build up.

## Before You Start

1. Read `FRAMEWORK.md` in the project root (skim pipeline overview and Phase 4 section).
2. Read key Phase 1 files:
   - `phase1_comprehension/research_logic.md` (what to implement — methods, training strategy, evaluation)
   - `phase1_comprehension/equations.md` (metric formulas and model equations)
   - `phase1_comprehension/quantitative_targets.json` (target values to reproduce)
3. Read key Phase 2 files:
   - `phase2_planning/replication_plan.md` (task ordering and strategy)
   - `phase2_planning/assumptions.md` (approved assumptions for ambiguous decisions)
4. Read key Phase 3 files:
   - `phase3_data/data_dictionary.md` (column names, types, meanings)
   - `phase3_data/data_validation.md` (any data discrepancies to be aware of)
   - `phase3_data/processed/` (the actual data files)
5. Read `phase3_data/GATE.md` for human feedback from Phase 3.
6. Create all output files in `phase4_implementation/`.
7. Use `bash tools/run.sh` for ALL Python execution.

## What You Must Produce

### Output 1: `src/config.py`

Central configuration:
```python
"""Shared configuration for the replication."""
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "phase3_data" / "processed"
RESULTS_DIR = Path(__file__).resolve().parent.parent / "results"
TABLES_DIR = RESULTS_DIR / "tables"
FIGURES_DIR = RESULTS_DIR / "figures"
PREDICTIONS_DIR = RESULTS_DIR / "raw_predictions"

# Create output directories
for d in [TABLES_DIR, FIGURES_DIR, PREDICTIONS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# Paper constants (from quantitative_targets.json)
VALIDATION_START = "1998-01-01"
# ... add others as needed
```

### Output 2: `src/data_loader.py`

Shared data loading and preprocessing:
- Load processed CSVs from Phase 3
- Apply any additional transformations needed for modelling
- Provide train/test split functions matching the paper's strategy
- This is imported by all model scripts — no code duplication

### Output 3: `src/metrics.py`

All evaluation metrics from `equations.md`:
- Implement every metric as a standalone function
- Each function takes `y_true` and `y_pred` (or `y_prob` for probabilistic metrics)
- Include docstrings with the formula
- Include a `compute_all_metrics()` function that returns a dictionary of all metrics

### Output 4: `src/test_metrics.py`

Unit tests for metrics:
- Test each metric against hand-calculated examples
- Test edge cases: all-positive predictions, all-negative, perfect classifier
- Run with: `bash tools/run.sh -m pytest src/test_metrics.py`

### Output 5: Model scripts — one per model

For each model/method in the paper, create `src/model_<name>.py`:

```python
"""<Model Name> implementation for <paper title> replication.

Implements: [brief description of what this model does]
Reference: [paper section/equation number]
"""

def train(data, **params):
    """Train the model. Returns trained model or parameters."""
    ...

def predict(model, data):
    """Generate predictions. Returns probabilities."""
    ...

def run(data_loader, metrics_module):
    """Full pipeline: train, predict, evaluate, save results."""
    # Load data
    # Train model (following paper's exact strategy)
    # Generate predictions for all forecast horizons
    # Compute all metrics
    # Save predictions to raw_predictions/
    # Return results dictionary
    ...
```

Requirements for each model:
- Follow the paper's training strategy precisely (expanding window, monthly retraining, etc.)
- Use approved assumptions from `assumptions.md` for ambiguous parameters
- Log decisions as comments: `# ASSUMPTION: using default sklearn parameters (assumption #3)`
- Save raw predictions (probabilities per day) to `results/raw_predictions/`

### Output 6: `src/run_all.py`

Master runner that executes everything:
```python
"""Run all models and generate all results tables and figures."""
# 1. Load data
# 2. Run each model
# 3. Compile results into tables matching the paper's format
# 4. Generate all figures
# 5. Save results_summary.json
# 6. Print summary to stdout
```

This script must be runnable end-to-end: `bash tools/run.sh src/run_all.py`

### Output 7: `results/tables/`

One CSV per results table in the paper:
- `table_N_replicated.csv` — matching the paper's table structure (same rows, columns, ordering)
- Include headers that match the paper's column names
- Values should be rounded to match the paper's precision (e.g., 2 decimal places if paper uses 2)

### Output 8: `results/figures/`

One PNG per figure in the paper:
- `figure_N_replicated.png` — attempting to match the paper's visual style
- Use appropriate axis labels, titles, legends
- Match the paper's color scheme if described; otherwise use a sensible default
- High resolution (150+ DPI)

### Output 9: `implementation_log.md`

Document everything:

```markdown
# Implementation Log

## Decisions Made
| # | Decision | Reason | Assumption Ref | Impact |
|---|----------|--------|----------------|--------|
| 1 | Used sklearn LogisticRegression with default solver | Paper doesn't specify solver | Assumption #5 | Low — solver shouldn't affect results significantly |
| 2 | ... | ... | ... | ... |

## Deviations from Paper
| # | What | Why | Expected Impact |
|---|------|-----|-----------------|
| 1 | Used monthly retraining instead of daily | Paper says "retrained monthly" but could mean monthly batches | Should be identical |

## Issues Encountered
| # | Issue | Resolution | Status |
|---|-------|------------|--------|
| 1 | Climatology model produces NaN for rare bin combinations | Used Laplace smoothing | Resolved |

## Baseline Smoke Test Results
| Model | Key Metric | Paper Value | Our Value | Status |
|-------|-----------|-------------|-----------|--------|
| Persistence (24hr, M-class) | Accuracy | 0.80 | ? | MATCH/CLOSE/DISCREPANT |
| ... | ... | ... | ... | ... |

(If any baseline diverges >10% from paper, STOP and document why before proceeding)
```

### Output 10: `results_summary.json`

Machine-readable results for Phase 5 comparison:

```json
{
  "tables": {
    "table_2": {
      "description": "M-class 24hr, threshold 0.5",
      "data": {
        "SWPC": {"Accuracy": 0.84, "Precision": 0.62, ...},
        "Persistence": {...},
        ...
      }
    },
    ...
  },
  "special_analyses": {
    "storm_after_calm": {
      "TP": 56, "FN": 10, "FP": 1257, "TN": 5735
    }
  }
}
```

Match the structure of `quantitative_targets.json` from Phase 1 so Phase 5 can compare them directly.

## Execution Order

Follow this order strictly:

1. **Config + data loader + metrics** — foundational code, no model logic
2. **Test metrics** — verify metrics are correct before using them
3. **Simplest baseline** (persistence) — validate the pipeline end-to-end with the trivial case
4. **Compare baseline to paper** — if >10% off on key metrics, STOP. Debug. Document.
5. **Remaining baselines** (climatology, Naive Bayes, logistic regression)
6. **SWPC evaluation** (this just evaluates existing forecasts, no model training)
7. **Results tables and figures** — compile everything into the paper's format
8. **Special analyses** (if any — e.g., "storm after the calm" scenario)
9. **results_summary.json** — machine-readable output

## Quality Standards

- **Baselines first.** Never skip to complex models. If baselines are wrong, everything is wrong.
- **Modular code.** Each model is a separate file. Shared logic lives in `data_loader.py` and `metrics.py`. No copy-paste between model files.
- **Reproducible.** `run_all.py` must produce identical results every time. Set random seeds where applicable.
- **Match the paper's format.** Results tables should have the same rows, columns, and ordering as the paper. This makes Phase 5 comparison trivial.
- **Document, don't guess.** If the paper is ambiguous, use the approved assumption. If there's no assumption for this case, document the decision in `implementation_log.md` and proceed with the most reasonable choice.
- **Sanity check everything.** All metrics should be in valid ranges. Precision + recall should be consistent with F1. Row/column counts should match expectations.
