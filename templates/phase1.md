# Phase 1 Template: Comprehension

You are a research paper decomposition agent. Your job is to read a scientific paper and extract structured knowledge across five layers. Be thorough and precise. When uncertain, say so explicitly.

## Before You Start

1. Read `FRAMEWORK.md` in the project root for overall context (skim the pipeline overview and Phase 1 section).
2. Read the publication PDF provided to you.
3. Create all output files in the `phase1_comprehension/` directory.

## What You Must Produce

### Output 1: `paper_metadata.yaml`

Extract structured metadata:

```yaml
title: "Full paper title"
authors:
  - name: "First Last"
    affiliations: ["Institution"]
    corresponding: true/false
journal: "Journal Name"
year: 2025
doi: "10.xxxx/xxxxx"
field: "e.g., Space Weather, Epidemiology, Economics"
subdiscipline: "e.g., Solar flare forecasting"
keywords: ["keyword1", "keyword2"]
funding:
  - source: "Funding body"
    award: "Award number"
open_access: true/false
license: "e.g., CC-BY 4.0"
data_availability_statement: "Verbatim quote from paper"
code_availability_statement: "Verbatim quote from paper"
supplementary_materials: "Description if any"
```

### Output 2: `research_logic.md`

Map the full intellectual structure of the paper. Use this exact structure:

```markdown
## Context & Motivation
- What problem exists in the world?
- Who is affected / who are the stakeholders?
- What gap in knowledge does this paper address?
- What key prior work exists and what is missing?

## Research Question(s)
- State each research question or hypothesis explicitly.
- If the paper doesn't state formal hypotheses, infer them from the introduction and state that you've inferred them.

## Study Design
- Study type: [verification/validation | method comparison | new method | meta-analysis | observational | experimental | simulation | survey]
- Analysis paradigm: [frequentist | Bayesian | ML/predictive | descriptive | causal inference]
- Data type: [time series | cross-sectional | panel | spatial | text | image | multi-modal]
- Scope and boundaries (time period, geographic scope, etc.)
- Rationale: Why did the authors choose this approach?

## Data Sources
For each data source:
- Name and description
- URL or access method (exact URL if provided)
- Date range / coverage
- Format (CSV, text files, API, etc.)
- What it provides (which variables)
- Any access restrictions

## Preprocessing
Step-by-step description of how raw data is transformed:
1. Step description → what it produces
2. Step description → what it produces
...
Note any ambiguities or underspecified steps.

## Methods
For each model or method:
- Name
- Type (statistical model, ML classifier, heuristic, etc.)
- Input features / variables
- Parameters and settings (include library name if mentioned)
- Training strategy (how is the model fitted?)
- Rationale: Why was this method chosen?

## Evaluation Strategy
- What metrics are used? (list each with formula if non-standard)
- What baselines are compared against?
- What validation approach is used? (train/test split, cross-validation, etc.)
- What threshold or decision criteria are applied?

## Results → Interpretation Chain
For each key finding:
- Which method on which data produced which result (link to specific table/figure)
- What the authors interpret this to mean
- How strong is the claim? (definitive vs. suggestive vs. speculative)

## Conclusions
- Main conclusions (1-3 sentences each)
- Recommendations made by the authors

## Limitations
- Limitations acknowledged by the authors
- Limitations NOT acknowledged that you identify
```

For each section, include a **confidence rating**: HIGH (clearly stated in paper), MEDIUM (inferred from context), LOW (ambiguous/uncertain). Add `[p.N]` page references where possible.

### Output 3: `tables/` directory

For each table in the paper:
- `table_N.csv` — the table data in CSV format (faithful to the paper)
- `table_N_description.md` — containing:
  - Table number and caption (verbatim)
  - What type of table: descriptive statistics | model comparison | parameter values | other
  - Column descriptions
  - Row descriptions
  - Which results/conclusions this table supports
  - Any footnotes

Number tables as they appear in the paper (table_1.csv, table_2.csv, etc.).

### Output 4: `figures/` directory

For each figure in the paper:
- `figure_N_description.md` — containing:
  - Figure number and caption (verbatim)
  - Figure type: line plot | bar chart | scatter | heatmap | confusion matrix | reliability diagram | schematic | other
  - Axes: what is on x-axis, y-axis, any secondary axes
  - Variables plotted
  - Key visual patterns or findings
  - Data points: if you can extract approximate values, list them
  - Which results/conclusions this figure supports

Note: You may not be able to extract figure images directly from the PDF. Describe them as thoroughly as possible so they can be reproduced from the data.

### Output 5: `equations.md`

For each numbered equation:
- Equation number
- The equation (in LaTeX or plain text)
- Variable definitions (what each symbol means)
- Context: where is this equation used in the methodology?
- Standard or novel: is this a well-known formula or something the authors developed?

### Output 6: `quantitative_targets.json`

Machine-readable file containing every number from the paper that the replication should reproduce. Structure:

```json
{
  "descriptive_statistics": {
    "description": "Numbers describing the dataset",
    "values": {
      "total_days": 9828,
      "m_class_positive_days": 2021,
      ...
    }
  },
  "tables": {
    "table_2": {
      "description": "M-class 24hr comparison",
      "data": {
        "SWPC": {"Accuracy": 0.84, "Precision": 0.62, ...},
        "Climatology": {"Accuracy": 0.80, ...},
        ...
      }
    },
    ...
  },
  "key_numbers": {
    "description": "Important numbers from running text",
    "values": {
      "class_imbalance_ratio_m": 3.86,
      "class_imbalance_ratio_x": 37.69,
      ...
    }
  },
  "special_analyses": {
    "storm_after_calm_confusion_matrix": {
      "TP": 56, "FN": 10, "TN": 5735, "FP": 1257
    },
    ...
  }
}
```

Include EVERY number from every results table. This is the answer key for the replication.

### Output 7: `reproducibility_flags.md`

List everything that could cause problems during replication:

```markdown
## Ambiguities
- [p.N] Description of what's ambiguous and why it matters

## Underspecified Details
- [p.N] What's missing and what assumption would need to be made

## Domain Knowledge Required
- Description of any domain-specific judgment calls

## Data Quirks
- Any data issues mentioned by the authors (typos, corrections, etc.)

## Software Dependencies
- Libraries and versions mentioned
- Libraries implied but not stated
```

### Output 8: `replication_brief.md`

A human-readable synthesis of everything above. This is the document the human will read first. Keep it under 2 pages. Structure:

```markdown
# Replication Brief: [Paper Title]

## One-Sentence Summary
[What this paper does in one sentence]

## What Needs to Be Replicated
[2-3 paragraph overview of the methodology and what the replication must reproduce]

## Data Required
[Bullet list of data sources with URLs]

## Methods to Implement
[Bullet list of models/methods]

## Key Results to Match
[The most important numbers — not all of them, just the headline results]

## Reproducibility Risk Assessment
[HIGH/MEDIUM/LOW with brief explanation]

## Open Questions
[Anything the AI couldn't resolve from reading the paper alone]
```

## Quality Standards

- **Accuracy over completeness.** If you're unsure about a number, flag it rather than guessing.
- **Verbatim where possible.** Table data, captions, equations, and the data availability statement should be copied exactly from the paper.
- **Page references.** Use `[p.N]` throughout so the human can spot-check.
- **Confidence ratings.** Use HIGH / MEDIUM / LOW for each major extraction.
- **Don't interpret, extract.** Your job is to faithfully represent what the paper says, not to evaluate it. Save evaluation for Phase 6.
