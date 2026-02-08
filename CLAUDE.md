# REPLIC-AI Project Memory

## Project
AI paper replication framework for Shoulders (founder's thought leadership content). 3-phase pipeline: Understand → Replicate → Synthesize.

## Key Files
- `FRAMEWORK.md` — orchestrator operating manual (v2, 3 phases)
- `templates/understand.md`, `replicate.md`, `synthesize.md` — sub-agent templates
- `replic.py` — lightweight git checkpoint/tag/status tool
- `tools/extract_pdf.py` — unified PDF extraction (gemini default, zai for high-fidelity OCR)
- `tools/run.sh` — venv wrapper. ALWAYS use `bash tools/run.sh` for Python, never bare `python3`

## Critical Rules
- **Never use bare python3/pip3.** Always `.venv/bin/python` via `tools/run.sh`. Python 3.14 and pip3 resolve to different Python versions on this machine.
- API keys in `.env` (gitignored): `GEMINI_API_KEY`, `ZAI_API_KEY`
- Default Gemini model: `gemini-3-flash-preview` (not the old 2.5 names)
- Z.ai GLM-OCR: requires base64 data URI for local files, not file paths

## Current State
- v2 framework complete and committed
- Gemini extraction done: `understand/extraction.md` (63K chars, solar flare paper)
- Z.ai extraction tested and working (82K chars, higher fidelity but noisier)
- Ready to run Phase 1 (UNDERSTAND) for real

## Test Paper
Camporeale & Berger (2025) "Verification of the NOAA SWPC Solar Flare Forecast (1998-2024)" — Space Weather journal. Evaluates SWPC probabilistic forecasts for M/X-class solar flares over 26 years against zero-cost baselines.
