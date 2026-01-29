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
 [Phase 6] EXTENSIONS ──────────> Extended Analysis
     |                            (robustness checks, new methods, critique)
     v  human checkpoint
 [Phase 7] REPORT ──────────────> Final Replication Report
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

**Purpose:** Download, parse, and clean all data. Validate against descriptive statistics reported in the paper.

**Input:** Resource inventory and replication brief.

**What the AI does:**
- Sets up a Python environment with required packages
- Downloads all datasets
- Parses raw files into structured format (DataFrames / CSVs)
- Handles format inconsistencies, encoding issues, missing values
- Constructs derived variables described in the paper (e.g., binary labels, rolling windows)
- Validates against the paper's reported descriptive statistics:
  - Sample sizes and date ranges
  - Class distributions
  - Summary statistics
- Saves cleaned data as CSV/parquet files
- Documents any discrepancies between expected and actual data

**Output:** Clean dataset files, a data validation report (`data_validation.md`), and the Python environment setup.

**Human checkpoint:** Do the data counts match the paper? If there are discrepancies, are they explainable (e.g., data updates since publication)? Is the environment set up correctly?

**Tools needed:** Python (pandas, numpy, requests, ftplib), web access.

**Prompt template:**
```
Using the resource inventory (resource_inventory.md) and replication brief
(replication_brief.md), set up a Python environment and acquire all
datasets. Parse raw files into clean DataFrames. Construct all derived
variables described in the paper. Validate against the paper's reported
sample sizes, class distributions, and descriptive statistics. Save
cleaned data as CSVs and document any discrepancies in data_validation.md.
```

---

### Phase 4: Implementation & Execution

**Purpose:** Implement all methods from the paper and generate results.

**Input:** Cleaned data, replication brief.

**What the AI does:**
- Implements each model/method described in the paper
- Follows the exact training strategy (e.g., cross-validation scheme, train/test splits)
- Computes all evaluation metrics
- Generates all figures and tables
- Saves all intermediate and final results
- Logs any implementation decisions where the paper was ambiguous

**Output:** Analysis code (Python scripts or notebooks), results tables (CSV), figures (PNG/PDF), and an implementation log (`implementation_log.md`) documenting decisions made.

**Human checkpoint:** Spot-check the code. Do the simplest models (e.g., baselines) produce sensible numbers? Are there obvious bugs?

**Tools needed:** Python (scikit-learn, scipy, matplotlib, seaborn, statsmodels — whatever the paper's methods require).

**Prompt template:**
```
Using the cleaned data and replication brief, implement all methods
described in the paper. Follow the exact training strategy. Compute all
evaluation metrics. Generate all figures and tables. Save results as
CSVs and figures as PNGs. Document any ambiguities or implementation
decisions in implementation_log.md. Start with the simplest model to
verify the pipeline works, then build up to the full analysis.
```

---

### Phase 5: Comparison

**Purpose:** Systematically compare replicated results against the paper's reported results.

**Input:** Own results, paper's reported results (from replication brief).

**What the AI does:**
- Creates side-by-side comparison tables (own results vs. paper)
- Computes differences and percentage deviations
- Classifies each result as: match (within tolerance), close (small deviation), or discrepant
- Hypothesizes explanations for discrepancies (data versioning, implementation differences, ambiguities in the paper)
- Identifies which conclusions from the paper are supported by the replication and which are not

**Output:** Comparison report (`comparison_report.md`) with tables and analysis.

**Human checkpoint:** Are the discrepancies acceptable? Do the main conclusions hold? Should any phase be re-run with corrections?

**Prompt template:**
```
Compare all replicated results against the paper's reported values. For
every table and key figure, create side-by-side comparisons. Classify
results as match/close/discrepant. Hypothesize explanations for any
discrepancies. Assess whether the paper's main conclusions are supported
by your replication. Save as comparison_report.md.
```

---

### Phase 6: Extensions

**Purpose:** Go beyond the paper. Identify weaknesses, run additional analyses, propose improvements.

**Input:** Completed replication, comparison report.

**What the AI does:**
- Identifies analyses the paper could have done but didn't
- Runs robustness checks (sensitivity to parameters, alternative metrics)
- Tests stronger models or alternative methods
- Adds confidence intervals or statistical tests where the paper only reports point estimates
- Proposes methodological improvements with evidence
- Critiques the paper's limitations section — are there limitations the authors missed?

**Output:** Extended analysis report (`extensions_report.md`) with additional figures, tables, and commentary.

**Human checkpoint:** Are the extensions sound? Are the critiques fair?

**Prompt template:**
```
With the replication complete, go beyond the paper. Identify missing
analyses, robustness checks, and methodological improvements. Implement
at least 3-5 extensions. Add confidence intervals where the paper
reports only point estimates. Test at least one stronger model. Critique
the paper's methodology and conclusions. Save as extensions_report.md.
```

---

### Phase 7: Report

**Purpose:** Produce a single, coherent replication report suitable for sharing.

**Input:** All outputs from previous phases.

**What the AI does:**
- Synthesizes everything into a structured report
- Includes: summary, methodology, replicated results, comparison, extensions, conclusions
- Highlights what worked, what didn't, and where the AI struggled
- Assesses overall replication success (full / partial / failed)

**Output:** Final report (`replication_report.md`).

**Prompt template:**
```
Synthesize all outputs from the replication into a final report. Include:
executive summary, methodology, replicated results with figures, comparison
against the paper, extensions and novel analyses, and an honest assessment
of replication success. Highlight where the AI succeeded and where it
struggled. Save as replication_report.md.
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
    raw/                        # Downloaded raw files
    processed/                  # Cleaned CSVs/parquets
    data_validation.md          # Validation against paper stats

  phase4_implementation/
    src/                        # Analysis code
    results/                    # Output tables and figures
    implementation_log.md       # Decisions and ambiguities

  phase5_comparison/
    comparison_report.md        # Side-by-side results

  phase6_extensions/
    extensions_report.md        # Additional analyses
    results/                    # Extension outputs

  phase7_report/
    replication_report.md       # Final synthesis
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
