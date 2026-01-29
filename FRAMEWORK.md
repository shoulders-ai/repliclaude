# REPLIC-AI: An AI Paper Replication Framework

## What This Is

A structured pipeline for using AI (Claude Code) to autonomously replicate published scientific papers. Each phase runs as a separate sub-agentic task or session with human review between phases. The human acts as a quality gate — checking outputs, deciding whether to proceed, and course-correcting when needed.

## The Premise

Most published research should be reproducible. In practice, replication is rare because it's tedious, unglamorous, and time-consuming. AI may change that. The question this framework explores: **how far can AI get on its own, and where does it break down?**

---

## Pipeline Overview

```
 PAPER (PDF) +/- DATA (CSV/JSON/etc. - optional)
     |
     v
 [Phase 1] COMPREHENSION ──────> Paper Knowledge Graph
     |                            (deep structured decomposition)
     v  human checkpoint
 [Phase 2] PLANNING ────────────> Replication Plan
     |                            (resource discovery, task breakdown,
     |                             risk assessment, strategy)
     v  human checkpoint
 [Phase 3] DATA ACQUISITION ────> Clean Datasets + Validation
     |                            (parsed, verified against paper)
     v  human checkpoint
 [Phase 4] IMPLEMENTATION ──────> Working Analysis Code + Results
     |                            (methods coded, executed, outputs saved)
     v  human checkpoint
 [Phase 5] COMPARISON ──────────> Comparison Report
     |                            (own results vs paper results)
     v  human checkpoint
 [Phase 6] FINAL REPORT ─────> Replication Report + Review
                                  (synthesis, critique, proposed extensions)
```

Claude Code Opus 4.5 acts as the **orchestrator**. It is responsible for:
- Calling `phase_gate.py` to manage transitions (start → commit → complete)
- Launching sub-agents via the Task tool with: "read `templates/phaseN.md` and `FRAMEWORK.md`, then do the work"
- Reviewing sub-agent outputs and writing GATE.md for human review
- Reading human additions to GATE.md and deciding how to proceed

**Sub-agents** do the actual work. They receive a focused prompt from the orchestrator, read their phase template from disk, and write output files. They never call phase_gate.py or manage transitions.

**The human** reviews GATE.md between phases, adds notes (never edits agent output), and says "proceed" or "redo."

Each phase transitions through: **start** (prerequisites validated) → **commit** (sub-agent work frozen in git) → **complete** (human approved, phase locked). See `WORKFLOW.md` for the full interaction flow.

Phase templates live in `templates/phaseN.md`. These are deterministic instruction sets that define exactly what each sub-agent must produce. The orchestrator does not rewrite or paraphrase templates — it tells the sub-agent to read the template file directly.

---

## Phase Details

### Phase 1: Comprehension

**Purpose:** Deep decomposition of the paper into a structured knowledge representation. This is the foundation — every subsequent phase depends on the quality of extraction here. The goal is not just summarisation but systematic disassembly of the paper into machine-usable components.

**Input:** The PDF file (and any supplementary materials if available).

**What the AI does:**

The AI reads the full paper and produces outputs across five extraction layers:

#### Layer 1: Metadata
- Title, authors, affiliations, corresponding author
- Journal, year, DOI, citation string
- Field / sub-discipline
- Funding sources and grants
- Keywords
- Open access status and license
- Data/code availability statement (verbatim)
- Supplementary materials references

#### Layer 2: Tables, Figures & Equations
This layer is critical for later comparison. Every table and figure must be extracted and decomposed.

**Tables:**
- Extract each table as a structured CSV file (machine-readable)
- Preserve column headers, row labels, units
- Include the table caption and any footnotes
- Note which tables contain results vs. descriptive/setup information

**Figures:**
- Extract each figure as an image file
- Write a structured description: figure type (line plot, bar chart, scatter, heatmap, schematic, confusion matrix, etc.), axes, variables plotted, key visual patterns
- Where possible, extract approximate data points from the figure
- Note which figures show results vs. methodology/setup

**Equations:**
- Extract each numbered equation with its context
- Note what each variable represents
- Flag which equations are standard (well-known formulas) vs. novel

#### Layer 3: Research Logic Chain
Map the intellectual structure of the paper. For quantitative research, this follows a general pattern:

```
Research Question / Hypothesis
    ↓
Study Design & Classification
    ↓
Data Sources → Variables → Preprocessing
    ↓
Methods / Models (each with parameters)
    ↓
Evaluation Strategy (metrics, baselines, validation)
    ↓
Results (linked to specific methods and data)
    ↓
Interpretation → Conclusions → Limitations
```

Each element should be explicitly linked. For example: "Hypothesis H1 is tested using Method M3 on Dataset D1, evaluated with Metrics E1 and E2, producing Results in Table 4, interpreted as supporting H1."

**Study classification** (helps the AI calibrate its approach):
- **Study type:** verification/validation, method comparison, new method proposal, meta-analysis, observational, experimental, simulation, survey
- **Analysis paradigm:** frequentist statistics, Bayesian, machine learning/predictive, descriptive, causal inference
- **Data type:** time series, cross-sectional, panel/longitudinal, spatial, text, image, multi-modal

#### Layer 4: Quantitative Targets
Every number that the replication should attempt to reproduce, structured for machine comparison:
- All values from all results tables (as structured JSON/CSV)
- Key numbers from running text (sample sizes, p-values, effect sizes, date ranges, thresholds)
- Descriptive statistics reported about the data (means, distributions, counts)
- These become the ground truth for Phase 5

#### Layer 5: Reproducibility Assessment
- What is explicitly specified vs. ambiguous or underspecified
- What requires domain expertise to fill in
- Software, libraries, and versions mentioned
- Known data quirks or edge cases mentioned by authors
- Potential reproducibility risks (e.g., "the paper says 'we cleaned the data' but doesn't specify how")

**Outputs:**

```
phase1_comprehension/
  paper_metadata.yaml           # Layer 1: structured metadata
  research_logic.md             # Layer 3: the full logic chain
  tables/
    table_N.csv                 # Layer 2: each table as structured data
    table_N_description.md      # Caption + context for each table
  figures/
    figure_N.png                # Layer 2: each figure as image
    figure_N_description.md     # Structured description of each figure
  equations.md                  # Layer 2: all equations with context
  quantitative_targets.json     # Layer 4: all numbers for comparison
  reproducibility_flags.md      # Layer 5: ambiguities and risks
  replication_brief.md          # Human-readable synthesis of all layers
```

**Human checkpoint:** This is the most important checkpoint. Review the replication brief and spot-check the extracted tables and logic chain. Key questions:
- Did the AI correctly identify all data sources?
- Is the research logic chain accurate? Are hypothesis-method-result links correct?
- Are the extracted tables faithful to the paper?
- Are there important ambiguities the AI missed?

Errors here cascade through everything downstream.

**Sub-agent template:** `templates/phase1.md` — contains detailed instructions and output format specifications for all five layers plus the synthesis brief.

**Orchestrator prompt to sub-agent:**
```
Before doing anything, read these files:
- templates/phase1.md (your detailed instructions — follow precisely)
- FRAMEWORK.md (overall context — skim the pipeline overview and Phase 1 section)

Then read publication.pdf and execute the template instructions.
Write all outputs to phase1_comprehension/.
```

The orchestrator adds any paper-specific context (e.g., "this is a space weather paper" or "the human has noted that supplementary data is available at URL X").

---

### Phase 2: Planning

**Purpose:** Transform the structured understanding from Phase 1 into an actionable replication plan. This phase includes resource discovery (checking what data/code is actually available) and then builds a concrete strategy informed by what's feasible.

This is a separate phase because replication is not always linear. Some papers require multiple iterations. Some data sources will be unavailable and need alternatives. Some methods are straightforward while others need careful sequencing. The plan should anticipate this.

**Input:** All Phase 1 outputs (especially `replication_brief.md`, `quantitative_targets.json`, `reproducibility_flags.md`).

**What the AI does:**

#### Step 1: Resource Discovery
- Checks every URL from the paper (are they live? do they return data?)
- Searches for the authors' code repository (GitHub, Zenodo, institutional pages)
- Searches for datasets on alternative mirrors if primary sources are down
- Identifies implicit data dependencies not cited in the paper
- Assesses accessibility: freely downloadable vs. requiring registration/API keys/payment
- Checks for supplementary materials, errata, corrigenda, or follow-up publications
- If authors' code exists, reviews it at a high level to understand their implementation choices

#### Step 2: Feasibility Assessment
- For each component of the paper, rate replication difficulty: straightforward / moderate / challenging / uncertain
- Identify the critical path: what must succeed for the replication to be meaningful?
- Identify quick wins: what can be validated first to build confidence the pipeline is working?
- Flag blockers: anything that could prevent replication entirely (missing data, proprietary tools, unclear methods)

#### Step 3: Strategy & Task Breakdown
- Choose the replication approach:
  - **Full replication:** reproduce everything end to end
  - **Partial replication:** focus on key results, skip peripheral analyses
  - **Progressive replication:** start with the simplest component, validate, then build up
- Break the work into concrete tasks with:
  - Clear success criteria (what does "done" look like for each task?)
  - Dependencies (what must be done before this task?)
  - Priority ordering (what to do first for maximum confidence?)
- Identify where iteration may be needed (e.g., "if parsing format A fails, try format B")

#### Step 4: Environment & Tooling Plan
- List required Python packages (or other tools)
- Note any specific library versions mentioned in the paper
- Plan the compute environment setup

**Outputs:**

```
phase2_planning/
  resource_inventory.md         # What's available: URLs, repos, data status
  data_sources.json             # Machine-readable source config with fallbacks
  feasibility_assessment.md     # Difficulty ratings, critical path, blockers
  replication_plan.md           # The strategy: approach, ordered tasks, success criteria
  environment_requirements.txt  # What to install
```

**Human checkpoint:** Review the plan. Key questions:
- Are the critical resources available? If not, are the fallbacks reasonable?
- Does the task ordering make sense? Should anything be prioritised differently?
- Are there blockers the AI didn't identify?
- Is the scope right? (Too ambitious? Too conservative?)

This is where the human can steer — e.g., "skip the 72-hour forecast analysis, focus on 24-hour" or "use the authors' preprocessed data rather than re-parsing raw files."

**Sub-agent template:** `templates/phase2.md` — contains detailed instructions for resource discovery, feasibility assessment, assumptions register, task breakdown, and decision points.

**Orchestrator prompt to sub-agent:**
```
Before doing anything, read these files:
- templates/phase2.md (your detailed instructions — follow precisely)
- FRAMEWORK.md (overall context — skim the pipeline overview and Phase 2 section)
- All files in phase1_comprehension/ (especially replication_brief.md,
  research_logic.md, quantitative_targets.json, reproducibility_flags.md,
  and GATE.md for human feedback)

Execute the template instructions. Write all outputs to phase2_planning/.
```

The orchestrator adds any context from the Phase 1 gate review (e.g., human corrections, decisions about scope).

---

### Phase 3: Data Acquisition & Validation

**Purpose:** Download, parse, and validate all data required for the replication. This phase is deliberately separate from implementation because data acquisition is the most fragile step — URLs break, formats change, servers go down. By isolating it, we can validate data integrity before writing any analysis code.

**Input:** All Phase 2 outputs (especially `data_sources.json`, `replication_plan.md`, `assumptions.md` with human approvals, `environment_requirements.txt`).

**What the AI does:**

#### Step 1: Environment Setup
- Install all packages from `environment_requirements.txt` into the project `.venv`
- Verify installations work (import each package)
- Log exact versions of every installed package

#### Step 2: Data Download
- Follow `data_sources.json` to download each source
- Use primary URLs first, fall back to alternatives if needed
- Save all raw files to `phase3_data/raw/` with clear naming
- Log download metadata: URL used, timestamp, file size, HTTP status codes
- Handle format-specific issues: FTP directory traversal, API pagination, encoding

#### Step 3: Data Parsing
- Parse raw files into structured DataFrames
- Handle format inconsistencies, encoding issues, missing values
- Document every parsing decision (e.g., "header on line 3, not line 1")
- Save intermediate parsed files for debugging

#### Step 4: Data Construction
- Construct all derived variables described in the paper (binary labels, rolling windows, merged datasets, etc.)
- Follow the exact preprocessing pipeline from `research_logic.md`
- Where the paper is ambiguous, follow the approved assumptions from `assumptions.md`
- Log every construction step

#### Step 5: Data Validation
- Compare against every descriptive statistic in `quantitative_targets.json` under `descriptive_statistics`
- Validate: sample sizes, date ranges, class distributions, summary statistics, missing value counts
- For each comparison: report expected value, actual value, match/mismatch, and explanation if different
- Check data integrity: no duplicate rows, dates in range, no impossible values

**Outputs:**

```
phase3_data/
  raw/                          # Downloaded raw files (untouched)
  processed/                    # Cleaned CSVs/parquets ready for analysis
  scripts/
    download.py                 # Reproducible download script
    parse.py                    # Raw → structured parsing
    construct.py                # Derived variable construction
  download_log.md               # URL, timestamp, size, status for each download
  data_dictionary.md            # Every column in every processed file: name, type, description, source
  data_validation.md            # Expected vs actual for every descriptive statistic
  data_summary.json             # Machine-readable summary stats for Phase 5 comparison
  environment_lock.txt          # pip freeze output — exact versions installed
  GATE.md
  MANIFEST.json
  conversation_log.md
```

**Human checkpoint:** Key questions:
- Do the data counts match the paper? If not, are discrepancies explainable (e.g., data updated since publication)?
- Are all data sources accounted for? Any that failed to download?
- Is the data dictionary clear enough that someone else could understand the processed files?
- Do the scripts run end-to-end without manual intervention?

**Sub-agent template:** `templates/phase3.md`

**Orchestrator prompt to sub-agent:**
```
Before doing anything, read these files:
- templates/phase3.md (your detailed instructions — follow precisely)
- FRAMEWORK.md (overall context — skim the pipeline overview and Phase 3 section)
- phase2_planning/data_sources.json (what to download and from where)
- phase2_planning/replication_plan.md (overall strategy)
- phase2_planning/assumptions.md (approved assumptions — check human decisions)
- phase2_planning/environment_requirements.txt (what to install)
- phase1_comprehension/research_logic.md (preprocessing steps)
- phase1_comprehension/quantitative_targets.json (validation targets)
- phase2_planning/GATE.md (human feedback from Phase 2)

Execute the template instructions. Write all outputs to phase3_data/.
Use bash tools/run.sh for all Python execution.
```

---

### Phase 4: Implementation & Execution

**Purpose:** Implement all methods from the paper and generate results. This is the core of the replication — translating the paper's methodology into working code that produces numerical outputs.

The sub-agent writes modular, testable code. Each method is a separate script or module. Results are saved as structured data (CSV/JSON), not just printed to console.

**Input:** All Phase 3 outputs (especially processed data files, `data_dictionary.md`), plus Phase 1 outputs (`research_logic.md`, `equations.md`, `quantitative_targets.json`) and Phase 2 outputs (`replication_plan.md`, `assumptions.md`).

**What the AI does:**

#### Step 1: Pipeline Scaffold
- Create a modular code structure: shared utilities, per-method scripts, a master runner
- Implement data loading and shared preprocessing as reusable functions
- Set up results output directories

#### Step 2: Metric Implementation
- Implement every evaluation metric from `equations.md`
- Write unit tests: verify each metric against known inputs/outputs
- Save as a reusable metrics module

#### Step 3: Baseline Models (Quick Wins)
- Start with the simplest models (persistence, climatology) to validate the pipeline
- Run on the data, compute metrics, compare against paper's values
- If baseline results diverge significantly: stop, diagnose, and document before proceeding
- This is the "smoke test" — if baselines are wrong, everything else will be too

#### Step 4: Full Model Implementation
- Implement each remaining model/method following the exact specifications in `research_logic.md`
- Follow the paper's training strategy precisely (expanding window, monthly retraining, etc.)
- Use approved assumptions from `assumptions.md` where the paper is ambiguous
- Log every implementation decision

#### Step 5: Results Generation
- Reproduce every results table from `quantitative_targets.json`
- Generate every figure described in Phase 1's `figures/` descriptions
- Run any special analyses (e.g., "storm after the calm" scenario)
- Save all results as structured CSV/JSON files

#### Step 6: Sanity Checks
- Verify results are internally consistent (e.g., precision and recall match F1)
- Check for obvious errors: all metrics in [0,1] range, no NaN results
- Compare simplest results against hand calculations

**Outputs:**

```
phase4_implementation/
  src/
    config.py                   # Paths, constants, shared configuration
    data_loader.py              # Data loading and shared preprocessing
    metrics.py                  # All evaluation metrics
    test_metrics.py             # Unit tests for metrics
    model_persistence.py        # Persistence baseline
    model_climatology.py        # Climatology baseline
    model_naive_bayes.py        # Naive Bayes
    model_logistic.py           # Logistic regression
    run_all.py                  # Master runner: executes all models, saves all results
  results/
    tables/
      table_N_replicated.csv    # Each results table from the paper
    figures/
      figure_N_replicated.png   # Each figure from the paper
    raw_predictions/
      model_X_predictions.csv   # Raw model outputs (for debugging)
  implementation_log.md         # Every decision, ambiguity, and deviation documented
  results_summary.json          # Machine-readable results for Phase 5
  GATE.md
  MANIFEST.json
  conversation_log.md
```

**Human checkpoint:** Key questions:
- Do baseline models produce sensible numbers? (This is the most important check)
- Does the code structure make sense? Could you follow the logic?
- Are there obvious bugs or suspicious results?
- Did the sub-agent flag any ambiguities that need human input?

**Sub-agent template:** `templates/phase4.md`

**Orchestrator prompt to sub-agent:**
```
Before doing anything, read these files:
- templates/phase4.md (your detailed instructions — follow precisely)
- FRAMEWORK.md (overall context — skim the pipeline overview and Phase 4 section)
- phase1_comprehension/research_logic.md (what to implement)
- phase1_comprehension/equations.md (metric formulas)
- phase1_comprehension/quantitative_targets.json (target values)
- phase2_planning/replication_plan.md (task ordering and strategy)
- phase2_planning/assumptions.md (approved assumptions)
- phase3_data/data_dictionary.md (what the data looks like)
- phase3_data/GATE.md (human feedback from Phase 3)

Execute the template instructions. Write all outputs to phase4_implementation/.
Use bash tools/run.sh for all Python execution.
Start with baselines. If baselines diverge >10% from paper values, stop and document why before proceeding.
```

---

### Phase 5: Comparison

**Purpose:** Systematically and quantitatively compare replicated results against the paper's reported results. This is the verdict — did the replication succeed? The comparison must be exhaustive, honest, and machine-readable.

**Input:** Phase 4 outputs (`results_summary.json`, all results tables and figures), Phase 1 outputs (`quantitative_targets.json`, all table descriptions).

**What the AI does:**

#### Step 1: Table-by-Table Comparison
- For every results table in the paper, create a side-by-side comparison: paper value | replicated value | difference | % deviation
- Classify each cell: MATCH (within rounding tolerance, ≤1%), CLOSE (2-10% deviation), DISCREPANT (>10% deviation)
- Compute aggregate match rates per table and overall

#### Step 2: Figure Comparison
- For every figure: generate the replicated version and place it alongside the paper's description
- Qualitatively assess: do the visual patterns match? Same trends, same relative ordering?
- Where figures contain specific values (axis annotations, data points), compare numerically

#### Step 3: Key Metric Comparison
- Focus on the paper's headline results (the numbers in the abstract and conclusions)
- These matter most — small deviations in peripheral tables are less important than deviations in key findings

#### Step 4: Discrepancy Analysis
- For every DISCREPANT result, hypothesize explanations:
  - Data versioning (data updated since publication)
  - Implementation difference (ambiguity resolved differently)
  - Bug in replication code
  - Possible error in the original paper
  - Rounding or precision differences
- Rank discrepancies by severity (does this affect the paper's conclusions?)

#### Step 5: Conclusion Assessment
- For each main conclusion in the paper (from `research_logic.md` → Conclusions section):
  - State the conclusion
  - State whether the replication supports, partially supports, or contradicts it
  - Cite specific evidence

**Outputs:**

```
phase5_comparison/
  comparison_tables/
    table_N_comparison.csv      # Side-by-side for each results table
  comparison_figures/
    figure_N_comparison.png     # Replicated figures (for visual comparison)
  comparison_report.md          # Full narrative analysis
  comparison_summary.json       # Machine-readable: per-table match rates, per-cell classifications
  discrepancy_register.md       # Every discrepancy with hypothesis and severity
  conclusion_assessment.md      # Paper's conclusions vs replication evidence
  GATE.md
  MANIFEST.json
  conversation_log.md
```

**Human checkpoint:** Key questions:
- Are the match rates acceptable? (>80% cells matching is good for a first replication)
- Do the main conclusions hold? This matters more than individual cell values
- Are discrepancy explanations plausible? Should any phase be re-run?
- Are there patterns in the discrepancies? (e.g., all X-class results off but M-class fine — suggests a data issue)

**Sub-agent template:** `templates/phase5.md`

**Orchestrator prompt to sub-agent:**
```
Before doing anything, read these files:
- templates/phase5.md (your detailed instructions — follow precisely)
- FRAMEWORK.md (overall context — skim the pipeline overview and Phase 5 section)
- phase1_comprehension/quantitative_targets.json (the paper's numbers — the ground truth)
- phase1_comprehension/research_logic.md (the paper's conclusions)
- phase1_comprehension/tables/ (original table descriptions)
- phase1_comprehension/figures/ (original figure descriptions)
- phase4_implementation/results_summary.json (your replicated numbers)
- phase4_implementation/results/tables/ (your replicated tables)
- phase4_implementation/implementation_log.md (decisions that might explain differences)
- phase4_implementation/GATE.md (human feedback from Phase 4)

Execute the template instructions. Write all outputs to phase5_comparison/.
```

---

### Phase 6: Final Report

**Purpose:** Produce the deliverable. A single, dense, factual report that synthesizes the entire replication: what was done, what was found, how well it matched, and what an AI agent that has deeply engaged with this paper thinks about it.

This phase does not run any new code or analysis. It reads everything from Phases 1-5 and writes.

The report must be concise and information-dense. No filler. Every sentence earns its place. Link to phase artifacts for detail rather than reproducing them inline. The human will edit this for voice and publish it.

**Input:** All outputs from all previous phases. Specifically:
- Every `GATE.md` file (the narrative of what happened at each phase, including human feedback)
- `phase1_comprehension/replication_brief.md` (what was attempted)
- `phase1_comprehension/research_logic.md` (the paper's full methodology)
- `phase1_comprehension/reproducibility_flags.md` (known weaknesses)
- `phase2_planning/assumptions.md` (decisions made under ambiguity)
- `phase3_data/data_validation.md` (did the data match?)
- `phase4_implementation/implementation_log.md` (decisions and struggles)
- `phase4_implementation/results_summary.json` (the replicated numbers)
- `phase5_comparison/comparison_report.md` (the verdict)
- `phase5_comparison/conclusion_assessment.md` (which conclusions held)
- `phase5_comparison/discrepancy_register.md` (what didn't match)

**What the AI does:**

#### Part 1: Process & Results Report
- Walk through each phase briefly: what was done, what happened, key decisions
- Present the replicated results alongside the paper's results (key tables only — link to full comparison)
- State the verdict: match rate, which conclusions held, major discrepancies and their explanations
- Document where the AI succeeded and struggled, where human intervention was needed
- Be factual and descriptive — no editorializing about the process

#### Part 2: Review & Proposed Extensions
Having spent 5 phases deeply inside this paper, the AI reviews it:
- Critique the methodology: strengths, weaknesses, assumptions that could be questioned
- Critique the interpretation: are conclusions well-supported or overreached?
- Propose specific extensions: robustness checks, sensitivity analyses, alternative methods, follow-on studies
- Each proposal: what to do, why it matters, what it would test. Concrete and actionable.
- These are suggestions only. Nothing is executed.

**Outputs:**

```
phase6_report/
  replication_report.md         # The deliverable — dense, factual, concise
  report_data.json              # Every number cited in the report (for fact-checking)
  GATE.md
  MANIFEST.json
  conversation_log.md
```

**Human checkpoint:** This is the final gate. Key questions:
- Is every number accurate and traceable to underlying phase outputs?
- Is the tone factual and calm? No AI hyperbole?
- Is it concise enough? Could anything be cut?
- Is the critique fair, evidence-based, and constructive?
- Are the proposed extensions interesting and actionable?
- Is this ready for you to edit and publish?

**Sub-agent template:** `templates/phase6.md`

**Orchestrator prompt to sub-agent:**
```
Before doing anything, read these files:
- templates/phase6.md (your detailed instructions — follow precisely)
- FRAMEWORK.md (overall context — skim the pipeline overview and Phase 6 section)
- ALL GATE.md files from phases 1-5 (the story of what happened)
- phase1_comprehension/replication_brief.md
- phase1_comprehension/research_logic.md
- phase1_comprehension/reproducibility_flags.md
- phase2_planning/assumptions.md
- phase3_data/data_validation.md
- phase4_implementation/implementation_log.md
- phase4_implementation/results_summary.json
- phase5_comparison/comparison_report.md
- phase5_comparison/conclusion_assessment.md
- phase5_comparison/discrepancy_register.md
- phase5_comparison/GATE.md

Execute the template instructions. Write all outputs to phase6_report/.
```

---

## Tooling Philosophy

### Language: Python

Python is the default for most computational science. The AI is most fluent in it. scikit-learn, pandas, numpy, matplotlib cover the vast majority of methods in empirical papers. If a paper uses R or MATLAB, the AI should still use Python unless the methods require language-specific packages.

### Core packages (install at Phase 3)

```
# Data handling
pandas, numpy, pyarrow

# Statistics and ML
scikit-learn, scipy, statsmodels

# Visualization
matplotlib, seaborn

# Data access
requests, beautifulsoup4, ftplib (stdlib)

# PDF/document processing (if needed)
pymupdf (fitz), tabula-py, pdfplumber

# Extras as needed per paper
xgboost, lightgbm, torch (if ML-heavy papers)
```

### Infrastructure

- **GitHub CLI** (`gh`) for repo operations and code discovery
- **Git** for version control of the replication project
- **Web access** for data downloads and resource verification
- **Local filesystem** for all outputs (no cloud dependencies)

---

## Project Structure

For each replication, the project directory should look like:

```
paper-replication/
  publication.pdf              # The paper
  README.md                    # Project overview
  FRAMEWORK.md                 # Orchestrator's operating manual
  WORKFLOW.md                  # Interaction flow documentation
  phase_gate.py                # Phase transition enforcement tool
  STATUS.md                    # Current pipeline state (auto-generated)
  LEDGER.md                    # Append-only transition log (auto-generated)

  templates/
    phase1.md                   # Sub-agent instructions for Phase 1
    phase2.md                   # Sub-agent instructions for Phase 2
    ...                         # (additional templates as needed)

  phase1_comprehension/
    paper_metadata.yaml         # Structured metadata
    research_logic.md           # Hypothesis → data → method → result chain
    tables/                     # Each table as CSV + description
    figures/                    # Each figure as image + description
    equations.md                # All equations with context
    quantitative_targets.json   # All numbers for comparison (machine-readable)
    reproducibility_flags.md    # Ambiguities, risks, gaps
    replication_brief.md        # Human-readable synthesis
    GATE.md                     # Orchestrator assessment + human review
    MANIFEST.json               # Phase lock (hashes, timestamps)
    conversation_log.md         # Conversation snapshot at completion

  phase2_planning/
    resource_inventory.md       # Data/code source availability
    data_sources.json           # Machine-readable source config + fallbacks
    feasibility_assessment.md   # Difficulty ratings, critical path, blockers
    assumptions.md              # Explicit assumptions requiring human approval
    replication_plan.md         # Strategy, ordered tasks, success criteria
    decision_points.md          # Questions for the human
    environment_requirements.txt # What to install
    GATE.md                     # Orchestrator assessment + human review
    MANIFEST.json               # Phase lock
    conversation_log.md         # Conversation snapshot

  phase3_data/
    raw/                        # Downloaded raw files (untouched)
    processed/                  # Cleaned CSVs/parquets ready for analysis
    scripts/
      download.py               # Reproducible download script
      parse.py                  # Raw → structured parsing
      construct.py              # Derived variable construction
    download_log.md             # URL, timestamp, size, status for each download
    data_dictionary.md          # Every column: name, type, description, source
    data_validation.md          # Expected vs actual for every descriptive stat
    data_summary.json           # Machine-readable summary stats
    environment_lock.txt        # pip freeze — exact versions installed
    GATE.md
    MANIFEST.json
    conversation_log.md

  phase4_implementation/
    src/
      config.py                 # Paths, constants, shared configuration
      data_loader.py            # Data loading and shared preprocessing
      metrics.py                # All evaluation metrics
      test_metrics.py           # Unit tests for metrics
      model_*.py                # One file per model/method
      run_all.py                # Master runner
    results/
      tables/                   # Replicated results tables (CSV)
      figures/                  # Replicated figures (PNG)
      raw_predictions/          # Raw model outputs
    implementation_log.md       # Decisions, ambiguities, deviations
    results_summary.json        # Machine-readable results for Phase 5
    GATE.md
    MANIFEST.json
    conversation_log.md

  phase5_comparison/
    comparison_tables/          # Side-by-side CSVs per table
    comparison_figures/         # Replicated figures for visual comparison
    comparison_report.md        # Full narrative analysis
    comparison_summary.json     # Per-table match rates, per-cell classifications
    discrepancy_register.md     # Every discrepancy with hypothesis and severity
    conclusion_assessment.md    # Paper's conclusions vs replication evidence
    GATE.md
    MANIFEST.json
    conversation_log.md

  phase6_report/
    replication_report.md       # The deliverable — dense, factual, concise
    report_data.json            # Every number cited (for fact-checking)
    GATE.md
    MANIFEST.json
    conversation_log.md
```

---

## What Makes a Paper Good for This?

Not every paper is equally suited for AI replication. The best candidates have:

- **Public data** — no proprietary or access-restricted datasets
- **Standard methods** — well-known algorithms, not bespoke simulations
- **Quantitative results** — tables of numbers that can be compared, not qualitative findings
- **Reproducibility artifacts** — code repos, supplementary data, clear method descriptions
- **Moderate complexity** — complex enough to be interesting, not so complex it requires months of domain expertise

---

## Honest Expectations

This framework will not produce perfect replications. Expected failure modes:

- **Data acquisition** is the most fragile step. URLs go stale, formats change, FTP servers go down.
- **Ambiguous methodology** in the paper leads to implementation choices that may differ from the authors'.
- **Domain-specific nuance** that the AI doesn't understand (e.g., the meaning of a 71% probability being a "typo" in solar flare data).
- **Complex preprocessing** pipelines that are described in one sentence but take days to implement correctly.
- **Slight numerical differences** due to library versions, floating point, or random seeds.

The value is not in perfect reproduction. It's in demonstrating how far autonomous AI can get, and where human expertise remains essential.
