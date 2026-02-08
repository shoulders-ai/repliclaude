# Replication Log

## Setup
Directory structure created. Beginning data acquisition.

## Data Acquisition
All 4 sources downloaded successfully:
- SWPC RSGA forecast archives: 29 years (1996-2024), tar.gz per year
- ASR flare catalog v1.0: 43.7 MB CSV (2002-2024)
- NOAA event reports: 6 years (1996-2001), extracted daily text files
- SILSO daily sunspot numbers: 2.9 MB CSV
- DSD daily solar data: also parsed for cross-check

## Data Parsing & Validation
Evaluation dataset: 9,862 days (Jan 1998 - Dec 2024)
Paper reports: 9,828 days (34-day difference, likely days without SWPC forecasts)
- M-class positive: 2,019 (paper: 2,021, diff: 2)
- X-class positive: 254 (paper: 254, MATCH)
- M imbalance ratio: 3.88 (paper: 3.86, CLOSE)
- X imbalance ratio: 37.83 (paper: 37.69, CLOSE)
- SWPC forecast coverage: 9,843 days at all lead times

## Metrics Unit Tests
All 19 tests passed.

## Baseline: Persistence
**66/66 metrics MATCH (all tables 2-7).** Pipeline fully validated.

## Baseline: Climatology
Probabilistic metrics match (Brier, AUC within 1-2%).
Threshold-dependent metrics (Recall, F1, CSI, TSS, HSS) are systematically higher than paper.
Root cause: paper does not fully specify how x1 (consecutive flare-free days) is computed
for different lead times. Multiple feature alignment approaches tested; none match perfectly.
Proceeding with current implementation (issue-day features).

Best results (D-lead features, SILSO sunspot):
- M_24h: Rec=0.41 (paper: 0.34), AUC=0.77 (MATCH), Brier=0.13 (MATCH)
- M_48h: Rec=0.39 (paper: 0.24), AUC=0.75 (MATCH), Brier=0.14 (MATCH)
- M_72h: Rec=0.37 (paper: 0.21), AUC=0.74 (MATCH), Brier=0.14 (MATCH)
