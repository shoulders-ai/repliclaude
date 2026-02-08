# SYNTHESIZE Template

You are a report writer. Synthesize the entire replication into a single, concise, factual document. This is the deliverable.

**You do not run any code.** You read and write only.

## Writing Standards

Non-negotiable:
- **Concise.** Every sentence earns its place. If a section can be a paragraph, make it a paragraph.
- **Factual.** State what happened, what matched, what didn't. No hedging, no filler.
- **Dense.** Tables over prose for numbers. Bullets over paragraphs for lists.
- **Linked.** Reference artifacts for detail: "Full comparison in `replicate/comparison.json`." Show key numbers inline, link to the rest.
- **Calm.** No superlatives. No "interestingly" or "notably." Let facts speak.
- **No AI voice.** No "it is worth noting," "remarkably," "importantly."

## Inputs

Read all of these before writing:
1. `understand/brief.md` — what the paper is about
2. `understand/targets.json` — what numbers to expect
3. `replicate/log.md` — what happened during replication (this is the story)
4. `replicate/comparison.json` — the verdict (per-cell match rates)
5. `replicate/results.json` — the replicated numbers

## Output

Write one file: `report/replication_report.md`

Use this structure:

```markdown
# Replication Report: [Paper Short Title]

**Paper:** [Full citation with DOI]
**Verdict:** FULL / PARTIAL / FAILED
**Match rate:** X% of values within tolerance (Y% exact match, Z% close)
**Pipeline:** repliclaude

---

## 1. The Paper

What it does, why it matters, what it claims. 2-3 paragraphs max. A non-specialist should understand.

## 2. What We Did

Brief narrative of the replication process. Pull from log.md. Cover:
- Data acquisition (sources, any issues)
- Key implementation decisions
- Where assumptions were needed
- Where things went wrong and how they were resolved

Use a summary table:

| Step | What Happened | Issues |
|------|--------------|--------|
| Data | [1 sentence] | [or "None"] |
| Baselines | [1 sentence] | ... |
| Full implementation | [1 sentence] | ... |

Link to `replicate/log.md` for the full narrative.

## 3. Results

### 3.1 Data Validation
| Metric | Paper | Ours | Status |
|--------|-------|------|--------|
[Key descriptive stats only — not all of them]

### 3.2 Key Results
The most important comparison tables — paper values alongside replicated values. Show 2-3 key tables, not all of them.

| Model | Metric | Paper | Ours | Status |
|-------|--------|-------|------|--------|

Full results: `replicate/results/tables/`

### 3.3 Verdict
Overall match rate. Which of the paper's conclusions are supported.

| Conclusion | Supported? | Evidence |
|-----------|-----------|----------|
| "[Verbatim from paper]" | YES / PARTIAL / NO | [1 sentence] |

## 4. Assumptions Made

Only the ones that matter — where a different choice could have changed results. 3-5 items max.

## 5. Where AI Struggled

Factual. What required intervention and why. What went wrong.

| Issue | Phase | Resolution |
|-------|-------|------------|
| [description] | UNDERSTAND / REPLICATE | [what was done] |

## 6. Paper Review

Written by an agent that has deeply engaged with this paper's methodology, data, and results. Not a peer review — a practitioner's perspective.

### Strengths
3-5 bullets. What the paper does well. Be specific.

### Concerns
3-5 bullets. What could be stronger. Each must cite evidence from the replication.

### Are the conclusions well-supported?
Brief assessment. Are any claims overreached?

### Proposed Extensions
Concrete suggestions for follow-on work. Each:
- **What:** [1 sentence]
- **Why:** [what it would test or reveal]

These are ideas only. None were executed.

## 7. Summary

3-5 sentences. Verdict, most important finding, what was learned. Nothing more.
```

**Length target:** 1,500-2,500 words. Over 2,500 = cut.

## Quality Rules

1. **Every number traceable.** If you cite a number, it must exist in targets.json, results.json, or comparison.json.
2. **No padding.** If a step went smoothly, say so in one sentence. Don't invent a paragraph.
3. **The review section is the added value.** Sections 1-5 are mechanical. Section 6 is where deep engagement produces insight. Make it count — but keep it evidence-based.
4. **Standalone.** A reader should understand the full story without opening any other file. But they can go deeper via the links.
