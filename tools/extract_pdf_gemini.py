#!/usr/bin/env python3
"""Extract structured content from a PDF using Gemini's native PDF understanding."""

import sys
import pathlib
import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv(pathlib.Path(__file__).resolve().parent.parent / ".env")

EXTRACTION_PROMPT = """\
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


def extract(pdf_path: str, output_path: str | None = None, model: str = "gemini-3-flash-preview") -> str:
    client = genai.Client()

    pdf = pathlib.Path(pdf_path)
    if not pdf.exists():
        print(f"ERROR: {pdf_path} not found", file=sys.stderr)
        sys.exit(1)

    print(f"Sending {pdf.name} ({pdf.stat().st_size // 1024}KB) to {model}...")

    response = client.models.generate_content(
        model=model,
        contents=[
            types.Part.from_bytes(data=pdf.read_bytes(), mime_type="application/pdf"),
            EXTRACTION_PROMPT,
        ],
    )

    result = response.text

    if output_path:
        out = pathlib.Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(result, encoding="utf-8")
        print(f"Written to {out} ({len(result)} chars)")
    else:
        print(result)

    return result


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: extract_pdf_gemini.py <pdf_path> [output_path] [model]")
        sys.exit(1)

    pdf = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else None
    mdl = sys.argv[3] if len(sys.argv) > 3 else "gemini-3-flash-preview"
    extract(pdf, out, mdl)
