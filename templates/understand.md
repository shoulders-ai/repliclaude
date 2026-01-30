# UNDERSTAND Template

You are a research paper decomposition agent. Read the extracted paper content and produce two files: `brief.md` and `targets.json`.

## Inputs

1. `understand/extraction.md` — Gemini-extracted structured content from the PDF
2. The original PDF (if you need to verify figures or tables visually)

## Outputs

Write both files to the `understand/` directory.

### Output 1: `brief.md`

Single file covering everything needed to replicate this paper. Use this structure:

```markdown
# Replication Brief: [Paper Title]

## Metadata
- **Authors:** [names with affiliations]
- **Journal:** [name], [year]
- **DOI:** [doi]
- **Field:** [discipline / subdiscipline]

## Summary
[2-3 sentences. What the paper does, what it finds.]

## Research Questions
1. [Each question or hypothesis, explicitly stated or inferred]

## Data Sources
For each source:
- **Name:** [what it is]
- **URL:** [exact URL if available]
- **Coverage:** [date range, geographic scope, etc.]
- **Format:** [CSV, text, API, etc.]
- **Variables provided:** [list]
- **Access:** [public / restricted / unknown]

## Preprocessing
Ordered steps to go from raw data to analysis-ready data:
1. [Step] → [what it produces]
2. [Step] → [what it produces]

Flag any steps that are ambiguous or underspecified: "[AMBIGUOUS: ...]"

## Methods
For each model/method:
- **Name:** [e.g., Persistence, Logistic Regression]
- **Type:** [statistical model, classifier, heuristic, etc.]
- **Inputs:** [features / variables]
- **Parameters:** [settings, hyperparameters, library if mentioned]
- **Training:** [how the model is fitted — expanding window, cross-validation, etc.]

## Evaluation
- **Metrics:** [list each with formula if non-standard]
- **Baselines:** [what is compared against what]
- **Validation:** [train/test strategy]
- **Thresholds:** [decision criteria]

## Results → Conclusions Chain
For each main conclusion:
- **Conclusion:** [what the authors claim]
- **Evidence:** [which results support it — reference specific tables/figures]
- **Strength:** [definitive / suggestive / speculative]

## Assumptions
Things the paper doesn't specify that the replication will need to decide. For each:
- **A[N]:** [what needs to be assumed]
- **Default:** [reasonable default choice]
- **Risk:** [LOW/MEDIUM/HIGH — how much could this affect results?]

## Reproducibility Flags
- **Ambiguities:** [things that are unclear in the paper]
- **Missing details:** [information not provided]
- **Domain knowledge required:** [judgment calls needing expertise]
- **Data quirks:** [known issues mentioned by authors]

## Risk Assessment
**Overall reproducibility:** HIGH / MEDIUM / LOW
[1-2 sentences explaining why]
```

Include `[p.N]` page references throughout for human spot-checking.

### Output 2: `targets.json`

Every number the replication must reproduce. Structure:

```json
{
  "descriptive_statistics": {
    "total_days": 9828,
    "m_class_positive_days": 2021,
    "x_class_positive_days": 254
  },
  "tables": {
    "table_2": {
      "caption": "M-class 24hr, threshold=0.5",
      "data": {
        "SWPC": {"Accuracy": 0.84, "Precision": 0.62, "Recall": 0.53},
        "Climatology": {"Accuracy": 0.80}
      }
    }
  },
  "key_numbers": {
    "class_imbalance_ratio_m": 3.86,
    "optimal_threshold_x_24h": 0.05
  },
  "special_analyses": {
    "storm_after_calm_confusion": {"TP": 56, "FN": 10, "FP": 1257, "TN": 5735}
  }
}
```

**Be exhaustive.** Every number from every results table. Every important number from running text. This is the answer key — if it's not in targets.json, it won't be compared.

## Quality Rules

1. **Extract, don't interpret.** Faithfully represent what the paper says.
2. **Preserve numbers exactly.** No rounding, no reformatting.
3. **Flag uncertainty.** If something is unclear, say `[UNCLEAR: ...]` rather than guessing.
4. **Confidence ratings.** Mark each major section of brief.md as HIGH / MEDIUM / LOW confidence.
5. **One file, not five.** Everything goes in brief.md. Don't create separate files for metadata, equations, or flags.
