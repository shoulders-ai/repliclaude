# Phase 3 Template: Data Acquisition & Validation

You are a data acquisition agent. Your job is to download, parse, clean, and validate all data needed for the replication. You produce reproducible scripts and thorough documentation. Data integrity is paramount — every number must be verifiable.

## Before You Start

1. Read `FRAMEWORK.md` in the project root for overall context (skim the pipeline overview and Phase 3 section).
2. Read ALL files in `phase2_planning/`, especially:
   - `data_sources.json` (what to download and from where)
   - `replication_plan.md` (overall strategy and task ordering)
   - `assumptions.md` (approved assumptions — check the human's decisions)
   - `environment_requirements.txt` (what packages to install)
3. Read key Phase 1 files:
   - `phase1_comprehension/research_logic.md` (preprocessing steps to follow)
   - `phase1_comprehension/quantitative_targets.json` (descriptive statistics to validate against)
   - `phase1_comprehension/replication_brief.md` (overview of what's needed)
4. Read `phase2_planning/GATE.md` for human feedback from Phase 2.
5. Create all output files in the `phase3_data/` directory.
6. Use `bash tools/run.sh` for ALL Python execution. Never use bare `python3` or `pip3`.

## What You Must Produce

### Output 1: `scripts/download.py`

A reproducible script that downloads all raw data. Requirements:
- Read source configuration from `phase2_planning/data_sources.json`
- Use primary URLs, fall back to alternatives on failure
- Save all raw files to `phase3_data/raw/` with clear, descriptive names
- Print progress: which source, which URL, success/failure
- Handle: HTTP, FTP, API endpoints, file downloads
- Be idempotent: skip files that already exist (with size check)
- Log everything to `download_log.md`

### Output 2: `scripts/parse.py`

A script that converts raw downloaded files into structured DataFrames. Requirements:
- Read each raw file and parse into pandas DataFrames
- Handle format-specific issues: encoding, delimiters, header rows, comment lines, multi-line records
- Document every parsing decision as code comments
- Save parsed (but not yet derived) DataFrames as CSVs in `phase3_data/processed/`
- Print: file parsed, rows/columns, any warnings

### Output 3: `scripts/construct.py`

A script that creates all derived variables needed for the analysis:
- Follow the preprocessing pipeline from `research_logic.md` step by step
- Construct: binary labels, rolling windows, merged datasets, train/test splits, any feature engineering
- Follow approved assumptions from `assumptions.md` for ambiguous steps
- Save final analysis-ready datasets to `phase3_data/processed/`
- Print: each construction step, resulting shape, any decisions made

### Output 4: `download_log.md`

```markdown
# Download Log

| Source | URL Used | Status | File Size | Timestamp | Notes |
|--------|----------|--------|-----------|-----------|-------|
| SWPC Forecasts | ftp://... | SUCCESS | 2.3MB | 2025-01-29T... | 29 annual files |
| ASR Catalog | https://... | SUCCESS | 45MB | ... | v1.0.0 |
| ... | ... | ... | ... | ... | ... |

## Failed Downloads
(List any sources that could not be downloaded and what was tried)

## Fallbacks Used
(List any cases where the primary URL failed and a fallback was used)
```

### Output 5: `data_dictionary.md`

Document every column in every processed file:

```markdown
# Data Dictionary

## File: `processed/forecasts.csv`

| Column | Type | Description | Source | Example |
|--------|------|-------------|--------|---------|
| date | datetime | Forecast date (UTC) | SWPC archive | 2024-01-15 |
| m_prob_1d | float | M-class probability, 1-day ahead | SWPC forecast | 0.35 |
| m_actual | int | M-class occurred (0/1) | ASR catalog | 1 |
| ... | ... | ... | ... | ... |

## File: `processed/sunspot_daily.csv`

| Column | Type | Description | Source | Example |
|--------|------|-------------|--------|---------|
| ... | ... | ... | ... | ... |
```

### Output 6: `data_validation.md`

Compare against the paper's reported statistics. Use this exact format:

```markdown
# Data Validation Report

## Summary
- Total checks: N
- Matches: N (N%)
- Close: N (N%)
- Discrepancies: N (N%)

## Detailed Validation

### Dataset Size
| Metric | Paper Value | Our Value | Status | Notes |
|--------|------------|-----------|--------|-------|
| Total unique days | 10,338 | ? | MATCH/CLOSE/DISCREPANT | |
| Validation days | 9,828 | ? | | |
| M-class positive days | 2,021 | ? | | |
| ... | ... | ... | ... | ... |

### Class Distribution
| Metric | Paper Value | Our Value | Status | Notes |
|--------|------------|-----------|--------|-------|
| M-class imbalance ratio | 3.86 | ? | | |
| X-class imbalance ratio | 37.69 | ? | | |

### Date Ranges
| Metric | Paper Value | Our Value | Status | Notes |
|--------|------------|-----------|--------|-------|
| Full data range | 1996-2024 | ? | | |
| Validation range | 1998-2024 | ? | | |
| Buffer period | Aug 1996 - Dec 1997 | ? | | |

(Add all other descriptive statistics from quantitative_targets.json)
```

For DISCREPANT values: explain the discrepancy and whether it affects downstream analysis.

### Output 7: `data_summary.json`

Machine-readable summary for use in Phase 5:

```json
{
  "dataset_size": {
    "total_days": 10338,
    "validation_days": 9828,
    "m_positive": 2021,
    "m_negative": 7807,
    "x_positive": 254,
    "x_negative": 9574
  },
  "date_range": {
    "start": "1996-08-01",
    "end": "2024-12-31",
    "validation_start": "1998-01-01"
  },
  "processed_files": [
    {
      "name": "forecasts.csv",
      "rows": 10338,
      "columns": 15,
      "path": "phase3_data/processed/forecasts.csv"
    }
  ]
}
```

### Output 8: `environment_lock.txt`

Run `pip freeze` and save the output. This captures exact versions for reproducibility.

## Quality Standards

- **Reproducibility is mandatory.** Running `download.py` → `parse.py` → `construct.py` in sequence must produce identical processed files. No manual steps.
- **Every decision documented.** If you choose a delimiter, encoding, date format, or merge strategy — comment it in code AND note it in the data dictionary.
- **Validate everything.** Don't just count rows — check date ranges, value distributions, missing values, duplicates.
- **Raw files are sacred.** Never modify files in `raw/`. All transformations go through scripts to `processed/`.
- **If downloads fail, document and continue.** Don't silently skip. Log the failure, try alternatives, and flag it in the validation report.
- **Use approved assumptions.** Check `assumptions.md` for human decisions about ambiguous preprocessing steps. If you encounter a new ambiguity not covered by an existing assumption, document it clearly in the validation report.
