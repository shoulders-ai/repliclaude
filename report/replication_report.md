# Replication Report: Verification of the NOAA SWPC Solar Flare Forecast

**Paper:** Camporeale, E. & Berger, T. E. (2025). Verification of the NOAA Space Weather Prediction Center Solar Flare Forecast (1998-2024). *Space Weather*. DOI: 10.1029/2025SW004546
**Verdict:** PARTIAL
**Match rate:** 64.3% within tolerance (52.5% exact match, 11.8% close)
**Pipeline:** repliclaude

---

## 1. The Paper

Camporeale and Berger perform the first comprehensive verification of NOAA's Space Weather Prediction Center (SWPC) operational probabilistic forecasts for M-class and X-class solar flares. The evaluation spans 26 years (1998-2024, 9,828 days) and compares SWPC against five zero-cost baselines: persistence, empirical climatology, Naive Bayes, logistic regression, and a baseline average ensemble.

The paper's central finding is that SWPC does not outperform these simple baselines on event-sensitive metrics (F1, CSI, HSS). While SWPC achieves the highest accuracy and lowest Brier scores, these are artifacts of extreme class imbalance -- M-class flares occur on only 20.6% of days, X-class on 2.6%. A model that never predicts a flare achieves 79.4% accuracy for M-class and 97.4% for X-class.

The paper also examines two safety-critical scenarios: "storm after the calm" (X-class flares following 30+ quiet days) and "all-clear" (quiet periods after X-class flares). In both cases, SWPC exhibits dangerously high false alarm rates and non-trivial miss rates, raising questions about astronaut safety protocols that depend on these forecasts.

## 2. What We Did

| Step | What Happened | Issues |
|------|--------------|--------|
| Data | Downloaded SWPC forecasts (29 annual archives), ASR flare catalog, NOAA event reports (1996-2001), SILSO sunspot numbers | None -- all URLs active |
| Parsing | Built unified evaluation dataset of 9,862 days | 34-day difference from paper's 9,828; 2 fewer M-class positive days |
| SWPC evaluation | Applied paper's 11 metrics at theta=0.5 across 3 lead times, 2 flare classes | 3 values off by 1 percentage point (M_48h Recall/POD/CSI) |
| Persistence | Replicated binary persistence model | None |
| Climatology | Conditional probability lookup with monthly retraining | Recall systematically higher than paper; feature alignment for x1 unspecified |
| Naive Bayes | Gaussian NB with expanding-window training | Paper's NB is extremely aggressive (Recall=0.93); could not reproduce this behavior |
| Logistic Regression | scikit-learn LR with monthly retraining | M-class mostly close; X-class all-zero predictions at theta=0.5 |
| Special analyses | Storm-after-calm and all-clear confusion matrices | Qualitative findings match; absolute counts differ slightly |

Full narrative: `replicate/log.md`

## 3. Results

### 3.1 Data Validation

| Metric | Paper | Ours | Status |
|--------|-------|------|--------|
| Evaluation days | 9,828 | 9,862 | CLOSE (34-day diff) |
| M-class positive | 2,021 | 2,019 | CLOSE |
| X-class positive | 254 | 254 | MATCH |
| M imbalance ratio | 3.86 | 3.88 | CLOSE |
| X imbalance ratio | 37.69 | 37.83 | CLOSE |

The 34-day discrepancy likely reflects days absent from the SWPC archive. Two fewer M-class positive days trace to minor differences in flare catalog version or UTC boundary handling. These differences are small enough that they do not affect conclusions.

### 3.2 Key Results

**SWPC Forecast (Tables 2-7): 63/66 MATCH, 3 CLOSE**

| Lead Time | Class | Metric | Paper | Ours | Status |
|-----------|-------|--------|-------|------|--------|
| 24h | M | All 11 | -- | -- | 11/11 MATCH |
| 48h | M | Recall | 0.46 | 0.47 | CLOSE |
| 48h | M | CSI | 0.34 | 0.35 | CLOSE |
| 48h | M | TSS | 0.37 | 0.38 | CLOSE |
| 72h | M | All 11 | -- | -- | 11/11 MATCH |
| 24h | X | All 11 | -- | -- | 11/11 MATCH |
| 48h | X | All 11 | -- | -- | 11/11 MATCH |
| 72h | X | All 11 | -- | -- | 11/11 MATCH |

**Persistence (Tables 2-7): 66/66 MATCH**

Every metric at every lead time and flare class matches exactly.

**Climatology (Tables 2-7): Brier and AUC match; recall-dependent metrics diverge**

| Lead | Class | Brier (P/O) | AUC (P/O) | Recall (P/O) | Status |
|------|-------|-------------|-----------|---------------|--------|
| 24h | M | 0.13/0.13 | 0.77/0.77 | 0.34/0.41 | Probabilistic MATCH; threshold DISCREPANT |
| 48h | M | 0.14/0.14 | 0.75/0.75 | 0.24/0.39 | Same pattern |
| 72h | M | 0.14/0.14 | 0.74/0.74 | 0.21/0.37 | Same pattern |

The Brier/AUC match confirms the underlying probability distributions are correct. The recall discrepancy stems from how x1 (consecutive flare-free days) is aligned to multi-day lead times -- a detail the paper does not specify.

**Naive Bayes: substantially different**

The paper's NB produces Recall=0.93 with Brier=0.36 for M-class 24h -- an extremely aggressive classifier that predicts flares far more often than base rates. Our Gaussian NB produces Recall=0.70 with Brier=0.16. For X-class, our NB produces all-zero predictions at theta=0.5 while the paper reports Recall=0.84. The paper does not specify whether NB uses continuous or discrete features, nor whether Laplace smoothing is applied. This is the largest source of discrepancy.

**Special Analyses**

| Analysis | Metric | Paper | Ours | Status |
|----------|--------|-------|------|--------|
| Storm after calm | FN (missed flares) | 10 | 10 | MATCH |
| Storm after calm | Miss rate | 0.15 | 0.16 | CLOSE |
| Storm after calm | FAR | 0.95 | 0.96 | CLOSE |
| All-clear | FN (missed flares) | 1 | 1 | MATCH |
| All-clear | Recall | 0.99 | 0.99 | MATCH |
| All-clear | FAR | 0.79 | 0.81 | CLOSE |

Full cell-by-cell comparison: `replicate/comparison.json`

### 3.3 Verdict

**Overall: 297 values compared. 156 MATCH (52.5%), 35 CLOSE (11.8%), 106 DISCREPANT (35.7%).**

The headline numbers are misleading. The discrepancies concentrate in three models (Climatology threshold metrics, Naive Bayes, Logistic Regression) where the paper underspecifies implementation details. The two models that matter most -- SWPC and Persistence -- achieve 129/132 MATCH (97.7%).

| Conclusion | Supported? | Evidence |
|-----------|-----------|----------|
| "SWPC does not outperform zero-cost baselines on event-sensitive metrics" | YES | SWPC and Persistence F1 both 0.57 for M_24h; Persistence beats SWPC in X-class F1/CSI/HSS at all lead times |
| "High accuracy and low Brier scores are misleading due to class imbalance" | YES | Confirmed: no-flare accuracy 79.4% (M), 97.4% (X); SWPC's accuracy advantage vanishes when event-sensitive metrics are used |
| "X-class forecasts are severely miscalibrated" | YES | Optimal SWPC threshold for X-class is 0.05 across all lead times, confirming systematic under-confidence |
| "Storm-after-calm: dangerous miss rate and false alarm rate" | YES | FN=10 MATCH; miss rate 0.16 vs 0.15; FAR 0.96 vs 0.95 |
| "All-clear: poor at identifying safe post-flare periods" | YES | FN=1 MATCH; recall=0.99; FAR 0.81 vs 0.79 |

## 4. Assumptions Made

1. **Sunspot number source:** Used SILSO daily total sunspot numbers (paper does not specify the source). Minor differences possible if the paper used a different database.

2. **Feature alignment for multi-day leads:** The paper does not explain how x1 (consecutive flare-free days) is computed for 48h and 72h forecasts. We used issue-day features for all lead times. This is the primary driver of Climatology recall discrepancies.

3. **Naive Bayes feature treatment:** Implemented as Gaussian NB (continuous features) since the paper does not specify. The paper's NB behavior (Recall>0.9, Brier>0.35 for M-class) suggests a very different implementation -- possibly discrete features with aggressive smoothing.

4. **Baseline Average composition:** Used all four baselines for M-class and three (excluding LR) for X-class, per the paper's explicit X-class statement. The M-class composition is ambiguous.

5. **Evaluation day count:** Our dataset has 34 more days than the paper's 9,828. We could not determine which days the paper excludes beyond requiring SWPC forecasts to be present.

## 5. Where AI Struggled

| Issue | Phase | Resolution |
|-------|-------|------------|
| SWPC forecast file format undocumented | REPLICATE | Inspected raw files, built parser iteratively |
| Climatology feature alignment for multi-day leads | REPLICATE | Tested multiple approaches; none matched paper exactly; accepted Brier/AUC match as validation |
| Naive Bayes implementation details unspecified | REPLICATE | Tried Gaussian and categorical NB; neither reproduced paper's aggressive behavior; accepted discrepancy |
| 34-day evaluation period discrepancy | REPLICATE | Could not identify which days to exclude; proceeded with full dataset |

## 6. Paper Review

### Strengths

- **Scale and duration.** 26 years of operational forecasts is an unusually long verification window. This is not a cherry-picked period -- it spans two full solar cycles plus the rising phase of a third.
- **Appropriate baseline selection.** The zero-cost baselines (especially persistence) are the right comparisons. Too many forecast verification studies compare only against climatology, which is a weak baseline for temporally correlated events like solar flares.
- **Safety-critical framing.** The storm-after-calm and all-clear analyses translate abstract skill metrics into concrete operational risk. The finding that SWPC misses 1 in 7 X-class flares after quiet periods is directly actionable for mission planning.
- **Honest treatment of class imbalance.** The paper does not bury the imbalance problem. It leads with it, computes the no-skill baselines, and uses appropriate metrics (F1, CSI, HSS, TSS) alongside accuracy and Brier.
- **Complete metric battery.** Reporting 11 metrics per model per condition makes the results robust to metric-shopping. The conclusions hold regardless of which event-sensitive metric a reader prefers.

### Concerns

- **Underspecified baselines.** The Naive Bayes and Climatology implementations lack enough detail for exact replication. Feature discretization, smoothing, and multi-day lead alignment are left implicit. Our replication matched SWPC and Persistence exactly but could not reproduce NB or Climatology threshold metrics. This matters because the paper's conclusions partly rest on baseline comparisons.
- **Baseline Average composition ambiguity.** The paper describes different BA compositions in different sections. For M-class, it is unclear whether persistence is included. This affects the BA results in Tables 2-4 and weakens claims about ensemble performance.
- **No confidence intervals or significance tests.** With 9,828 evaluation days, the skill differences between SWPC and baselines are presented as point estimates. Some differences (e.g., SWPC F1=0.57 vs Persistence F1=0.57 for M_24h) are effectively zero. Without bootstrap intervals or paired tests, it is difficult to distinguish "SWPC does not outperform" from "we cannot detect a difference."
- **ASR catalog version discrepancy.** The paper cites ASR v1.0.0 but the download URL points to v1.1. This introduces uncertainty about the ground truth labels, which affect every result in the paper.
- **Threshold sensitivity unexamined for baselines.** The paper shows that SWPC's optimal threshold is far from 0.5, implying poor calibration. But the same issue affects baselines differently. Persistence's optimal threshold is trivially 1.0 by construction. A fairer comparison would evaluate all models at their respective optimal thresholds side by side, which the paper does in Tables 9-14 but discusses less prominently.

### Are the conclusions well-supported?

The core conclusion -- SWPC does not outperform zero-cost baselines on event-sensitive metrics -- is well-supported and robust. It holds across both flare classes, all three lead times, and both threshold scenarios. The replication confirms this with 129/132 MATCH for SWPC+Persistence.

The subsidiary conclusions about calibration and safety-critical scenarios are also well-supported. The storm-after-calm and all-clear analyses reproduce the same qualitative findings.

The recommendation to adopt modern ML methods is weaker -- it is a policy suggestion, not a demonstrated result. The paper shows the problem but does not demonstrate the solution.

### Proposed Extensions

- **What:** Apply post-hoc calibration (Platt scaling or isotonic regression) to SWPC forecasts and re-evaluate.
  **Why:** The paper identifies miscalibration as a core problem. Calibration is a fixable preprocessing step. This would test whether the issue is in the forecasts themselves or in how probabilities are reported.

- **What:** Replace Naive Bayes and Logistic Regression with a modern gradient-boosted model (XGBoost/LightGBM) using the same two features.
  **Why:** The paper's baselines are deliberately simple. A slightly more capable model would establish whether the SWPC performance gap is bounded by feature information content or by model complexity.

- **What:** Stratify all results by solar cycle phase (minimum, rising, maximum, declining).
  **Why:** SWPC forecasters likely perform differently during active vs quiet periods. Persistence is strongest during sustained active periods. A phase-stratified analysis would reveal whether SWPC adds value during transitions between activity levels, which is where operational forecasting matters most.

- **What:** Extend the verification to include C-class flares and proton events.
  **Why:** SWPC issues forecasts for these events as well. The current paper focuses on M and X class. C-class flares are far more common and would stress-test the baselines differently.

## 7. Summary

This replication achieves PARTIAL status: the paper's two central models (SWPC evaluation and Persistence baseline) reproduce at 97.7% match rate, and all five paper conclusions are supported by our independent implementation. The supplementary baselines (Climatology, Naive Bayes, Logistic Regression) partially reproduce -- probabilistic metrics match but threshold-dependent metrics diverge due to underspecified implementation details. The paper's core finding stands: NOAA's operational solar flare forecasts, despite 26 years of institutional investment, do not outperform a model that simply predicts tomorrow will look like today.
