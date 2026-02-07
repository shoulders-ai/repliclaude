#!/usr/bin/env python3
"""
PDF extraction tool for REPLIC-AI.

Two backends:
  gemini  — Structured markdown extraction via Gemini (default).
             Best for: clean readable output, figure descriptions, overall comprehension.
             Models: gemini-3-flash-preview (fast/cheap), gemini-3-pro-preview (higher quality)

  zai     — High-fidelity OCR via Z.ai GLM-OCR.
             Best for: verifying specific table cells, bounding-box-level accuracy,
             scanned documents, complex multi-column layouts.
             Outputs both markdown and raw JSON with per-element coordinates.

Usage:
  extract_pdf.py <pdf_path> <output_path>                    # Gemini Flash (default)
  extract_pdf.py <pdf_path> <output_path> --backend gemini   # Gemini Flash
  extract_pdf.py <pdf_path> <output_path> --backend gemini --model gemini-3-pro-preview
  extract_pdf.py <pdf_path> <output_path> --backend zai      # Z.ai GLM-OCR
"""

import sys
import pathlib
import os
import json
import argparse
from dotenv import load_dotenv

load_dotenv(pathlib.Path(__file__).resolve().parent.parent / ".env")

# ── Gemini backend ──────────────────────────────────────────────────────────

GEMINI_PROMPT = """\
You are a precise scientific document extractor. Given this PDF, produce a single Markdown document with the following sections in order:

## Metadata
- Title, authors, journal, DOI, year, affiliations.

## Abstract
The full abstract, verbatim.

## Full Text
The complete body text in Markdown. Preserve section headings as Markdown headings (##, ###).
Preserve all in-text citations (e.g., Author et al., 2020).

## Tables
For EACH table in the paper:
### Table N: <caption>
Reproduce the table as a Markdown table. Every number must be EXACTLY as printed — do not round or reformat.
If a table spans multiple pages, merge it into one.

## Equations
For EACH numbered equation:
### Equation N
$$<LaTeX>$$
Describe variables and their meaning.

## Figures
For EACH figure:
### Figure N: <caption>
Describe what the figure shows in detail: axes, data series, trends, key values, annotations.
If the figure contains numerical values (axis ticks, annotations), include them.

## Key Numerical Results
List every quantitative result mentioned in the paper (p-values, coefficients, skill scores, percentages, sample sizes, date ranges, thresholds). Format as a bullet list. Be exhaustive — miss nothing.

CRITICAL RULES:
- Never invent or hallucinate content. Only extract what is in the PDF.
- Preserve ALL numbers exactly as printed. No rounding.
- If something is unclear, say "[UNCLEAR IN SOURCE]".
- For tables: prefer Markdown tables. If a table is too complex, use CSV format in a code block.
"""


def extract_gemini(pdf_path: pathlib.Path, output_path: pathlib.Path, model: str) -> str:
    from google import genai
    from google.genai import types

    print(f"[gemini] Sending {pdf_path.name} ({pdf_path.stat().st_size // 1024}KB) to {model}...")

    client = genai.Client()
    response = client.models.generate_content(
        model=model,
        contents=[
            types.Part.from_bytes(data=pdf_path.read_bytes(), mime_type="application/pdf"),
            GEMINI_PROMPT,
        ],
    )

    result = response.text
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(result, encoding="utf-8")
    print(f"[gemini] Written to {output_path} ({len(result)} chars)")
    return result


# ── Z.ai backend ───────────────────────────────────────────────────────────

def extract_zai(pdf_path: pathlib.Path, output_path: pathlib.Path) -> str:
    import base64
    from zai import ZaiClient

    api_key = os.environ.get("ZAI_API_KEY")
    if not api_key:
        print("ERROR: ZAI_API_KEY not set in .env", file=sys.stderr)
        sys.exit(1)

    print(f"[zai] Sending {pdf_path.name} ({pdf_path.stat().st_size // 1024}KB) to GLM-OCR...")

    client = ZaiClient(api_key=api_key)
    pdf_b64 = base64.b64encode(pdf_path.read_bytes()).decode("utf-8")
    data_uri = f"data:application/pdf;base64,{pdf_b64}"

    response = client.layout_parsing.create(model="glm-ocr", file=data_uri)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Save raw JSON (has bounding boxes, per-element data)
    raw_path = output_path.with_suffix(".raw.json")
    raw_path.write_text(
        json.dumps(response.model_dump(), indent=2, default=str), encoding="utf-8"
    )
    print(f"[zai] Raw JSON saved to {raw_path}")

    # Extract and save markdown
    md_text = ""
    if hasattr(response, "md_results") and response.md_results:
        md_text = response.md_results
    output_path.write_text(md_text, encoding="utf-8")
    print(f"[zai] Markdown saved to {output_path} ({len(md_text)} chars)")
    return md_text


# ── CLI ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Extract PDF content for REPLIC-AI")
    parser.add_argument("pdf", help="Path to PDF file")
    parser.add_argument("output", help="Output file path (.md)")
    parser.add_argument(
        "--backend", choices=["gemini", "zai"], default="gemini",
        help="Extraction backend (default: gemini)"
    )
    parser.add_argument(
        "--model", default="gemini-3-flash-preview",
        help="Gemini model (default: gemini-3-flash-preview). Ignored for zai backend."
    )
    args = parser.parse_args()

    pdf = pathlib.Path(args.pdf)
    if not pdf.exists():
        print(f"ERROR: {args.pdf} not found", file=sys.stderr)
        sys.exit(1)

    output = pathlib.Path(args.output)

    if args.backend == "gemini":
        extract_gemini(pdf, output, args.model)
    elif args.backend == "zai":
        extract_zai(pdf, output)


if __name__ == "__main__":
    main()
