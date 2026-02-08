# Replication Brief: Verification of the NOAA Space Weather Prediction Center Solar Flare Forecast (1998-2024)

## Metadata
- **Authors:** Enrico Camporeale (Queen Mary University of London; Space Weather Technology, Research and Education Center, University of Colorado Boulder), Thomas E. Berger (National Center for Atmospheric Research, High Altitude Observatory, Boulder, CO)
- **Journal:** Space Weather, 2025
- **DOI:** 10.1029/2025SW004546
- **Field:** Space Weather / Solar Physics / Forecast Verification

## Summary
This study performs the first comprehensive verification of NOAA SWPC's operational probabilistic forecasts for M-class and X-class solar flares over 26 years (1998-2024), comprising 9,828 evaluation days. The authors compare SWPC forecasts against zero-cost baselines (persistence, climatology, Naive Bayes, logistic regression, and a baseline average ensemble) and find that SWPC does not outperform these simple methods on event-sensitive metrics (F1, CSI, HSS), exhibits severe calibration issues especially for X-class flares, and has dangerously high false alarm rates in critical "storm after the calm" and "all-clear" scenarios relevant to astronaut safety. [p.1-2]

**Confidence: HIGH**

## Research Questions
1. How skillful are the SWPC probabilistic flare forecasts for M-class and X-class events over the 26-year period 1998-2024? [p.1-2]
2. Do SWPC forecasts outperform zero-cost and simple statistical baselines (persistence, climatology, Naive Bayes, logistic regression)? [p.1-2]
3. How well-calibrated are the SWPC probabilistic forecasts (reliability analysis)? [p.7]
4. What are the optimal probability thresholds for SWPC forecasts to maximize TSS, and what does this reveal about calibration? [p.9]
5. How does SWPC perform in the critical "storm after the calm" scenario -- detecting the first X-class flare after >30 days of quiet? [p.11]
6. How does SWPC perform in the "all-clear" scenario -- correctly identifying safe periods 1-3 days after an X-class flare? [p.11-12]

**Confidence: HIGH**

## Data Sources

### Source 1: SWPC Daily Probabilistic Forecasts
- **Name:** NOAA SWPC historical flare forecast archive
- **URL:** ftp://ftp.swpc.noaa.gov/pub/warehouse/ [p.3]
- **Coverage:** 1996-2024 (annual text files); evaluation period starts January 1998 [p.3-4]
- **Format:** Annual text files, parsed into unified CSV; each row = one date with six forecast probabilities (1/2/3-day ahead for M- and X-class) [p.3]
- **Variables provided:** Date, M-class forecast probability (24h, 48h, 72h), X-class forecast probability (24h, 48h, 72h) -- all as integer percentages [p.3]
- **Access:** Public (FTP)
- **Notes:** Discrete probability values. M-class uses {1, 5, 10, 15, ..., 95} (20 values). X-class 24hr uses {1, 2, 5, 10, ..., 75} except 65, 70 (15 values). X-class 48hr uses {1, 2, 5, 10, ..., 75} except 65 (16 values). X-class 72hr uses {1, 2, 5, 10, ..., 75} except 70 (16 values). One known typo: 2007-09-04 had probabilities 71/71/71 for M-class, changed to 70/70/70. [p.7-8]

### Source 2: ASR Flare Catalog (for 2002-2024)
- **Name:** ASR (Archival Solar Flares) catalog v1.0.0
- **URL:** https://github.com/helio-unitov/ASR_cat/releases/download/v1.1/f_1995_2024.csv [p.2]
- **Coverage:** 2002-2024 flare events [p.3]
- **Format:** CSV
- **Variables provided:** Flare events with class, date/time, location, associated active region [p.2-3]
- **Access:** Public (GitHub)
- **Notes:** Released 12 March 2025 by Berretti et al. (2025). The paper says "ASR v1.0.0" but the download URL says "v1.1" -- this may be a version discrepancy. [UNCLEAR: The paper states v1.0.0 but the URL points to v1.1 release; unclear which was actually used] [p.2]

### Source 3: NOAA SWPC Event Reports (for 1996-2001)
- **Name:** NOAA SWPC event reports
- **URL:** ftp://ftp.swpc.noaa.gov/pub/indices/events/ [p.3]
- **Coverage:** 1996-2001 flare events [p.3]
- **Format:** Text files
- **Variables provided:** Flare event records including class and date/time [p.3]
- **Access:** Public (FTP)

### Source 4: Sunspot Numbers
- **Name:** Sunspot number data (used as feature x2 for baseline models) [p.6]
- **URL:** [UNCLEAR: not explicitly stated; likely from SILSO or NOAA but no URL given] [p.6]
- **Coverage:** 1996-2024 (daily values needed for the full period) [p.6]
- **Format:** [UNCLEAR: not specified]
- **Variables provided:** Daily sunspot number [p.6]
- **Access:** Public (likely)

**Confidence: MEDIUM** -- The sunspot number source is not explicitly identified. The ASR catalog version discrepancy (v1.0.0 vs v1.1 URL) introduces minor uncertainty.

## Preprocessing
Ordered steps to go from raw data to analysis-ready data:

1. **Parse SWPC forecast files** -- Read annual text files from ftp://ftp.swpc.noaa.gov/pub/warehouse/, extract daily forecast probabilities (M-class and X-class at 24h, 48h, 72h). Compile into unified CSV with one row per date and six probability columns. [p.3] -> Produces: `swpc_forecasts.csv`

2. **Clean forecast data** -- Fix known typo: change 2007-09-04 M-class probabilities from 71/71/71 to 70/70/70. [p.7-8] -> Produces: cleaned forecast CSV

3. **Parse flare occurrence records** -- For 2002-2024: use ASR catalog CSV. For 1996-2001: parse NOAA SWPC event reports text files. [p.3] -> Produces: unified flare event list

4. **Construct binary ground truth labels** -- For each day, create binary label (0/1) for M-class and X-class separately. A day is positive (1) if at least one flare of that class occurred during that day (UTC). Number of flares per day is not relevant; only binary occurrence matters. [p.3-4] -> Produces: `daily_labels.csv` with columns: date, M_label, X_label

5. **Merge forecasts and labels** -- Join forecast probabilities with ground truth labels on date. The merged dataset spans 10,338 unique days. [p.4] -> Produces: `merged_dataset.csv`

6. **Split training buffer from evaluation period** -- Reserve first 17 months (August 1996 to December 1997) as training buffer only. Evaluation period: January 1998 to December 2024 = 9,828 days. [p.4, p.6-7] -> Produces: evaluation dataset

7. **Compute derived features for baseline models** -- For each day, compute: x1 = number of consecutive prior flare-free days (separately for M and X), x2 = sunspot number on that day. [p.6] -> Produces: feature-augmented dataset

8. **Discretize features for climatology model** -- Bin x1 (consecutive flare-free days) into: {0, 1, 2, ..., 20, >20}. Bin x2 (sunspot number) into: {0, 10, 20, ..., 200, >200}. [p.6] -> Produces: binned features for climatology lookup

[AMBIGUOUS: The exact format/structure of the annual SWPC text files is not described. Parsing logic must be inferred or discovered from the raw files.]

[AMBIGUOUS: How sunspot numbers are obtained and aligned to dates is not detailed. The source database for daily sunspot numbers is not specified.]

[AMBIGUOUS: For the 1996-2001 NOAA event reports, the parsing procedure to extract M/X flare events is not detailed.]

**Confidence: MEDIUM** -- The preprocessing steps are logically clear but several mechanical details (file formats, parsing logic, sunspot source) are left implicit.

## Methods

### Method 1: SWPC Forecast (the system under test)
- **Name:** NOAA SWPC Operational Forecast
- **Type:** Operational probabilistic forecast (McIntosh classification-based with human forecaster adjustments) [p.2]
- **Inputs:** Active region classifications, recent flaring activity, expert judgment, supplementary model outputs [p.2]
- **Parameters:** Not publicly documented in detail. Issues integer probability percentages for M-class and X-class at 24h, 48h, 72h lead times. [p.2]
- **Training:** Not applicable (this is the operational system being evaluated). Issued at 22:00 UTC daily, incorporated into 3-day forecast at 00:30 UTC, updated at 12:30 UTC. [p.2]
- **Notes:** Methodology begins with McIntosh classification, assigns climatological probabilities, then human forecasters adjust based on region evolution, recent activity, and expert judgment. [p.2]

### Method 2: Persistence Model
- **Name:** Persistence
- **Type:** Heuristic baseline [p.5-6]
- **Inputs:** Binary flare occurrence on the current day [p.5-6]
- **Parameters:** None
- **Training:** None required [p.5-6]
- **Logic:** For each day D, the observed flare activity (binary: M or X class occurred today) is used as the prediction for D+1, D+2, D+3. This is a deterministic (0/1) model. [p.5-6]

### Method 3: Empirical Climatology
- **Name:** Climatology (Clim.)
- **Type:** Conditional probability lookup table [p.6]
- **Inputs:** x1 = consecutive flare-free days, x2 = sunspot number [p.6]
- **Parameters:** Discretization bins: x1 in {0, 1, 2, ..., 20, >20}, x2 in {0, 10, 20, ..., 200, >200} [p.6]
- **Training:** Monthly retraining using expanding window. For each month's forecasts, train only on all prior months. First used starting January 1998 (after 17-month buffer). [p.6-7]
- **Formula:** P_clim(y=1 | x1 in b1, x2 in b2) = N_flare(b1, b2) / N_total(b1, b2) (Equation 1) [p.6]

### Method 4: Naive Bayes
- **Name:** Naive Bayes (NB)
- **Type:** Probabilistic classifier assuming conditional independence [p.6]
- **Inputs:** x1 = consecutive flare-free days, x2 = sunspot number [p.6]
- **Parameters:** [UNCLEAR: discretization details for NB not explicitly stated; likely same binning as climatology or continuous]
- **Training:** Monthly retraining using expanding window, same as climatology. [p.6-7]
- **Formula:** P(y=1|x1,x2) = P(y=1)P(x1|y=1)P(x2|y=1) / sum over y' of P(y')P(x1|y')P(x2|y') (Equation 2) [p.6]

### Method 5: Logistic Regression
- **Name:** Logistic Regression (LR)
- **Type:** Linear probabilistic classifier [p.6]
- **Inputs:** x1 = consecutive flare-free days, x2 = sunspot number [p.6]
- **Parameters:** Coefficients beta_0, beta_1, beta_2 [p.6]
- **Training:** Monthly retraining using expanding window, same as climatology. [p.6-7]
- **Formula:** log(P/(1-P)) = beta_0 + beta_1*x1 + beta_2*x2 (Equation 3); P = sigmoid (Equation 4) [p.6]
- **Notes:** Excluded from X-class Baseline Average due to poor calibration and negligible recall. [p.10]

### Method 6: Baseline Average (BA)
- **Name:** Baseline Average
- **Type:** Simple ensemble (average of component model probabilities) [p.8-9]
- **Inputs:** Predictions from component models [p.8-9]
- **Parameters:** None beyond component models
- **Training:** Inherits from component models
- **Composition for M-class:** Average of Climatology, Persistence, Naive Bayes, and Logistic Regression [p.8-9, inferred from Tables 2-4 including LR]
  [UNCLEAR: The exact composition is not explicitly stated for M-class. The text says "averaging the predictions of climatology, persistence, and Naive Bayes" for X-class. For M-class, the text in Section 4.4 says BA "combines... climatology, Naive Bayes, and logistic regression" but this omits persistence. Tables 2-4 include all 6 models. The composition may differ between M and X class.]
- **Composition for X-class:** Average of Climatology, Persistence, and Naive Bayes (LR excluded). [p.9-10]

**Confidence: MEDIUM** -- The exact composition of the Baseline Average for M-class is ambiguous. The paper mentions different subsets in different sections. The Naive Bayes discretization is not fully specified.

## Evaluation

### Metrics
All formulas given in Section 3.1 [p.4-5]:
- **Accuracy (ACC):** (TP + TN) / (TP + FP + TN + FN)
- **Precision (PREC):** TP / (TP + FP)
- **Recall / POD (REC):** TP / (TP + FN)
- **False Alarm Ratio (FAR):** FP / (TP + FP) = 1 - Precision
- **False Positive Rate (FPR):** FP / (FP + TN)
- **F1 Score:** 2 * PREC * REC / (PREC + REC) = 2*TP / (2*TP + FP + FN)
- **Critical Success Index (CSI):** TP / (TP + FP + FN)
- **True Skill Statistic (TSS):** TP/(TP+FN) - FP/(FP+TN)
- **Heidke Skill Score (HSS):** 2(TP*TN - FN*FP) / ((TP+FN)(FN+TN) + (TP+FP)(FP+TN))
- **Brier Score (BS):** (1/N) * sum((p_i - y_i)^2) -- lower is better [p.5-6]
- **AUC:** Area under ROC curve [p.5]

### Baselines
SWPC is compared against 5 models: Persistence, Climatology, Naive Bayes, Logistic Regression, and Baseline Average. [p.5-6]
- For X-class analysis with theta=0.5, Logistic Regression is excluded from comparison (poor performance). [p.9-10]

### Validation / Train-Test Strategy
- **Training buffer:** First 17 months (August 1996 - December 1997) used only for model initialization. [p.6-7]
- **Evaluation period:** January 1998 - December 2024 (9,828 days). [p.4]
- **Retraining:** Monthly rolling retraining -- each month's forecasts use a model trained on all prior months only. No future data leakage. [p.6-7]
- **Persistence:** No training required. [p.6]

### Thresholds
Two threshold scenarios [p.7]:
1. **Standard threshold (theta = 0.5):** Results in Tables 2-7.
2. **Optimized threshold (maximize TSS):** Optimal theta values in Table 8. Results in Tables 9-14. Each model's threshold is independently optimized. [p.9]

**Confidence: HIGH**

## Results -> Conclusions Chain

### Conclusion 1: SWPC forecasts do not outperform zero-cost baselines on event-sensitive metrics
- **Conclusion:** SWPC forecasts perform comparably to, or are outperformed by, simple statistical baselines across most skill metrics, especially event-sensitive ones (F1, CSI, HSS). [p.8-10, p.12]
- **Evidence:** Tables 2-7 (theta=0.5): BA consistently matches or beats SWPC in F1, CSI, HSS for M-class. Persistence beats SWPC in F1, CSI, HSS for X-class. Tables 9-14 (optimized threshold): performance gap narrows or disappears. [p.8-10]
- **Strength:** Definitive -- supported by 13 tables across multiple lead times, flare classes, and threshold choices.

### Conclusion 2: SWPC's high accuracy and low Brier scores are misleading due to class imbalance
- **Conclusion:** SWPC achieves highest accuracy and lowest Brier scores but these are inflated by the extreme class imbalance (M-class: 20.6% positive; X-class: 2.6% positive). A "never predict flare" model gets 79.4% accuracy for M-class and 97.4% for X-class. [p.7-8]
- **Evidence:** Table 1 (class imbalance ratios 3.86 and 37.69). Tables 2-7 showing SWPC's accuracy/Brier leadership but poor F1/CSI/HSS. [p.4, p.8]
- **Strength:** Definitive -- mathematically demonstrated.

### Conclusion 3: SWPC X-class forecasts are severely miscalibrated
- **Conclusion:** Optimal TSS threshold for SWPC X-class is 0.05 (vs. ideal 0.50), indicating systematic under-confidence requiring extreme post-processing. [p.9-10]
- **Evidence:** Table 8 showing optimal thresholds. Reliability diagrams (Figure 4) showing X-class overconfidence above 20% predicted probability. [p.7-8, p.9]
- **Strength:** Definitive

### Conclusion 4: SWPC fails critically in "storm after the calm" scenario
- **Conclusion:** When the Sun has been quiet >30 days, SWPC (at optimal 5% threshold) misses 15% of X-class flares (10 out of 66) and has a 95% false alarm ratio (1,257 false alarms out of 1,313 positive predictions). [p.11]
- **Evidence:** Figure 5 confusion matrix: TP=56, FN=10, FP=1,257, TN=5,735. [p.11]
- **Strength:** Definitive -- directly computed from data subset.

### Conclusion 5: SWPC fails in "all-clear" scenario for post-flare periods
- **Conclusion:** For days 1-3 after an X-class flare, SWPC correctly identifies only 38 out of 614 true quiet days, with precision of 0.21 and FAR of 0.79. [p.11-12]
- **Evidence:** Figure 6 confusion matrix: TP=150, FN=1, FP=576, TN=38. [p.11-12]
- **Strength:** Definitive

### Conclusion 6: Modern data-driven methods should supplement or replace current approaches
- **Conclusion:** SWPC and other operational offices should adopt multi-model ensemble approaches incorporating ML methods, and all new models should be verified using standardized metrics before deployment claims. [p.12-13]
- **Evidence:** Cumulative evidence from all analyses. [p.12-13]
- **Strength:** Suggestive -- this is a recommendation, not a proven result.

**Confidence: HIGH**

## Assumptions
Things the paper does not specify that the replication will need to decide:

- **A1: Sunspot number data source**
  - **Default:** Use SILSO daily total sunspot number from the Royal Observatory of Belgium (most standard source)
  - **Risk:** LOW -- Sunspot numbers are well-standardized across sources, though minor version differences may exist.

- **A2: Baseline Average composition for M-class**
  - **Default:** Average of all four baselines (Climatology, Persistence, Naive Bayes, Logistic Regression) for M-class; average of three (Climatology, Persistence, Naive Bayes) for X-class
  - **Risk:** MEDIUM -- The paper is ambiguous about M-class BA composition. Section 4.2.1 mentions BA without specifying components for M-class. Section 4.4 says "climatology, Naive Bayes, and logistic regression" (omitting persistence). The X-class composition explicitly excludes LR. Different compositions will produce different results.

- **A3: Naive Bayes feature discretization**
  - **Default:** Use same bins as climatology (x1: 0-20 plus >20; x2: 0-200 in steps of 10 plus >200) for the conditional probability distributions
  - **Risk:** MEDIUM -- The paper does not specify how Naive Bayes handles feature distributions. Could be continuous (kernel density) or discrete (binned). Different choices affect results.

- **A4: How to handle persistence for probabilistic metrics (Brier, AUC)**
  - **Default:** Persistence outputs binary 0/1, so Brier score is computed with p_i in {0, 1}. AUC is computed treating the binary output as the score.
  - **Risk:** LOW -- The paper reports Brier and AUC for persistence (e.g., Brier=0.18, AUC=0.73 for M-class 24h), confirming it is treated as a probabilistic forecast with p in {0,1}.

- **A5: SWPC forecast file parsing details**
  - **Default:** Inspect raw files to determine format; the paper says "annual text files" with forecast probabilities parsed into CSV.
  - **Risk:** MEDIUM -- Format may have changed over 26 years. Parsing errors could propagate to all results.

- **A6: UTC day boundary for flare labeling**
  - **Default:** A flare is assigned to the UTC date of its peak flux
  - **Risk:** LOW -- The paper explicitly states "at least one flare of that class occurred during that day (UTC)" [p.3-4].

- **A7: How monthly retraining works exactly**
  - **Default:** At the start of each month, retrain using all data from the buffer through the end of the previous month. Issue predictions for the entire current month using that trained model.
  - **Risk:** LOW -- The paper describes this clearly: "each month's forecasts are produced using a model trained only on data from all previous months" [p.6-7].

- **A8: Logistic regression implementation**
  - **Default:** Use scikit-learn LogisticRegression with default parameters
  - **Risk:** LOW -- Standard method, unlikely to differ significantly.

- **A9: How persistence handles 2-day and 3-day forecasts**
  - **Default:** Same binary value (today's flare occurrence) is used as the prediction for D+1, D+2, and D+3
  - **Risk:** LOW -- Paper explicitly states this [p.5-6].

**Confidence: HIGH**

## Reproducibility Flags

### Ambiguities
- The exact composition of the Baseline Average model for M-class flares is inconsistent across sections. [p.8-9 vs p.10]
- The ASR catalog version cited (v1.0.0) does not match the download URL (v1.1). [p.2]
- The discrete probability values for X-class forecasts have some ambiguity (e.g., "except for 65, 70" for X-24hr, "except for 65" for X-48hr, "except for 70" for X-72hr). The exact enumeration is not fully explicit. [p.7-8]
- Whether Naive Bayes uses binned or continuous feature distributions is not stated. [p.6]

### Missing Details
- Sunspot number source not identified (URL, version, or database name). [p.6]
- SWPC annual text file format not documented (column structure, delimiters, header conventions). [p.3]
- The NOAA SWPC event report format for 1996-2001 is not documented. [p.3]
- How "consecutive flare-free days" (x1) is computed at the start of the dataset (before the buffer period) is not discussed. [p.6]
- Logistic regression hyperparameters (regularization, solver) not specified. [p.6]
- Whether Naive Bayes uses Laplace smoothing or other techniques for zero-count bins is not stated. [p.6]

### Domain Knowledge Required
- Understanding GOES X-ray flare classification (A, B, C, M, X classes and subclasses). [p.1]
- Familiarity with McIntosh active region classification scheme. [p.2]
- Knowledge of solar cycle phases to validate temporal patterns in results. [p.3-4]
- Understanding of operational forecast verification methodology and proper scoring rules. [p.4-6]

### Data Quirks
- 2007-09-04 SWPC forecast typo (71% changed to 70% for M-class). [p.7-8]
- Extreme class imbalance: M-class 20.6% positive, X-class 2.6% positive. [p.4]
- 17-month buffer (Aug 1996 - Dec 1997) excluded from evaluation but needed for model initialization. [p.6-7]
- Persistence threshold is always 1.0 by construction (binary output). [p.9]
- FTP data sources may be unreliable or have been reorganized since paper publication. [p.3]

**Confidence: HIGH**

## Risk Assessment
**Overall reproducibility: MEDIUM-HIGH**

The core methodology is straightforward -- standard classification metrics applied to publicly available forecast and flare catalog data. The main risks are: (1) data acquisition from FTP sources that may be reorganized or unavailable, (2) ambiguity in the Baseline Average composition for M-class, (3) unspecified sunspot number source, and (4) parsing complexity of 26 years of heterogeneous SWPC text files. The statistical methods are all standard and well-documented. Given public data availability and standard metrics, we expect to match 80-90% of table values within close tolerance, with potential discrepancies arising from data version differences (especially ASR v1.0.0 vs v1.1) and BA composition assumptions.
