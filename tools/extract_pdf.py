#!/usr/bin/env python3
"""
extract_pdf.py — Programmatic PDF decomposition for REPLIC-AI.

Extracts text, tables, and images from a PDF into structured files
that sub-agents can read and process.

Usage:
    python tools/extract_pdf.py publication.pdf phase1_comprehension/pdf_extraction/

Produces:
    output_dir/
      full_text.md          — Complete text, page by page
      pages/
        page_01.md          — Text from each page
      tables/
        page_03_table_01.csv — Each detected table as CSV
      figures/
        page_03_img_01.png  — Each extracted image
      extraction_report.md  — Summary of what was extracted and quality notes
"""

import argparse
import csv
import io
import json
import sys
from pathlib import Path

try:
    import fitz  # pymupdf
except ImportError:
    print("ERROR: pymupdf not installed. Run: pip install pymupdf")
    sys.exit(1)

try:
    import pdfplumber
except ImportError:
    print("ERROR: pdfplumber not installed. Run: pip install pdfplumber")
    sys.exit(1)


def extract_text(pdf_path: Path, output_dir: Path):
    """Extract text from each page using pymupdf."""
    pages_dir = output_dir / "pages"
    pages_dir.mkdir(parents=True, exist_ok=True)

    doc = fitz.open(str(pdf_path))
    all_text_parts = []
    page_stats = []

    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text("text")

        # Save individual page
        page_file = pages_dir / f"page_{page_num + 1:02d}.md"
        page_file.write_text(f"# Page {page_num + 1}\n\n{text}")

        all_text_parts.append(f"---\n## Page {page_num + 1}\n\n{text}")

        page_stats.append({
            "page": page_num + 1,
            "chars": len(text),
            "has_text": len(text.strip()) > 0,
        })

    # Save full text
    full_text = f"# Full Text Extraction: {pdf_path.name}\n\n" + "\n".join(all_text_parts)
    (output_dir / "full_text.md").write_text(full_text)

    doc.close()
    return page_stats


def extract_tables(pdf_path: Path, output_dir: Path):
    """Extract tables using pdfplumber."""
    tables_dir = output_dir / "tables"
    tables_dir.mkdir(parents=True, exist_ok=True)

    table_stats = []

    with pdfplumber.open(str(pdf_path)) as pdf:
        for page_num, page in enumerate(pdf.pages):
            tables = page.extract_tables()
            if not tables:
                continue

            for table_idx, table in enumerate(tables):
                if not table or not any(any(cell for cell in row) for row in table):
                    continue  # skip empty tables

                # Clean cells
                cleaned = []
                for row in table:
                    cleaned_row = []
                    for cell in row:
                        if cell is None:
                            cleaned_row.append("")
                        else:
                            # Normalize whitespace
                            cleaned_row.append(" ".join(str(cell).split()))
                    cleaned.append(cleaned_row)

                # Write CSV
                filename = f"page_{page_num + 1:02d}_table_{table_idx + 1:02d}.csv"
                csv_path = tables_dir / filename
                with open(csv_path, "w", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerows(cleaned)

                table_stats.append({
                    "file": filename,
                    "page": page_num + 1,
                    "rows": len(cleaned),
                    "cols": max(len(row) for row in cleaned) if cleaned else 0,
                })

    return table_stats


def extract_images(pdf_path: Path, output_dir: Path):
    """Extract images using pymupdf."""
    figures_dir = output_dir / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)

    doc = fitz.open(str(pdf_path))
    image_stats = []

    for page_num in range(len(doc)):
        page = doc[page_num]
        images = page.get_images(full=True)

        for img_idx, img_info in enumerate(images):
            xref = img_info[0]
            try:
                base_image = doc.extract_image(xref)
                if base_image is None:
                    continue

                image_bytes = base_image["image"]
                ext = base_image.get("ext", "png")
                width = base_image.get("width", 0)
                height = base_image.get("height", 0)

                # Skip tiny images (likely icons or artifacts)
                if width < 50 or height < 50:
                    continue

                filename = f"page_{page_num + 1:02d}_img_{img_idx + 1:02d}.{ext}"
                img_path = figures_dir / filename
                img_path.write_bytes(image_bytes)

                image_stats.append({
                    "file": filename,
                    "page": page_num + 1,
                    "width": width,
                    "height": height,
                    "format": ext,
                    "size_kb": len(image_bytes) // 1024,
                })
            except Exception as e:
                image_stats.append({
                    "file": f"FAILED_page_{page_num + 1}_img_{img_idx + 1}",
                    "page": page_num + 1,
                    "error": str(e),
                })

    doc.close()
    return image_stats


def write_report(output_dir: Path, pdf_name: str, page_stats, table_stats, image_stats):
    """Write extraction summary report."""
    lines = [
        f"# PDF Extraction Report: {pdf_name}",
        "",
        f"## Summary",
        f"- **Pages:** {len(page_stats)}",
        f"- **Tables extracted:** {len(table_stats)}",
        f"- **Images extracted:** {len([i for i in image_stats if 'error' not in i])}",
        f"- **Image extraction failures:** {len([i for i in image_stats if 'error' in i])}",
        "",
        "## Pages",
        "",
        "| Page | Characters | Has Text |",
        "|------|-----------|----------|",
    ]
    for ps in page_stats:
        lines.append(f"| {ps['page']} | {ps['chars']} | {'Yes' if ps['has_text'] else 'No'} |")

    lines.extend(["", "## Tables", ""])
    if table_stats:
        lines.extend([
            "| File | Page | Rows | Cols |",
            "|------|------|------|------|",
        ])
        for ts in table_stats:
            lines.append(f"| {ts['file']} | {ts['page']} | {ts['rows']} | {ts['cols']} |")
    else:
        lines.append("No tables detected by pdfplumber.")

    lines.extend(["", "## Images", ""])
    if image_stats:
        lines.extend([
            "| File | Page | Size | Dimensions | Format |",
            "|------|------|------|------------|--------|",
        ])
        for im in image_stats:
            if "error" in im:
                lines.append(f"| {im['file']} | {im['page']} | ERROR | — | {im['error']} |")
            else:
                lines.append(f"| {im['file']} | {im['page']} | {im['size_kb']}KB | {im['width']}x{im['height']} | {im['format']} |")
    else:
        lines.append("No images extracted.")

    lines.extend([
        "",
        "## Quality Notes",
        "",
        "- **Text extraction:** pymupdf `get_text('text')` — generally reliable for well-structured PDFs. May struggle with multi-column layouts, equations, or unusual fonts.",
        "- **Table extraction:** pdfplumber — works best on tables with visible borders. May miss borderless tables or merge cells incorrectly. **Sub-agent should verify extracted tables against the paper.**",
        "- **Image extraction:** pymupdf `extract_image` — extracts embedded raster images. May not capture vector graphics, charts rendered as paths, or figures composed of multiple overlapping elements. **Sub-agent should use the Read tool on extracted images to visually verify.**",
        "",
        "The sub-agent should treat these extractions as best-effort starting points, not ground truth. Cross-reference against the full text and use multimodal reading of images where needed.",
    ])

    (output_dir / "extraction_report.md").write_text("\n".join(lines))

    # Also save stats as JSON for programmatic use
    stats = {
        "pages": page_stats,
        "tables": table_stats,
        "images": image_stats,
    }
    (output_dir / "extraction_stats.json").write_text(json.dumps(stats, indent=2))


def main():
    parser = argparse.ArgumentParser(description="Extract text, tables, and images from a PDF")
    parser.add_argument("pdf", help="Path to the PDF file")
    parser.add_argument("output", help="Output directory")
    args = parser.parse_args()

    pdf_path = Path(args.pdf)
    output_dir = Path(args.output)

    if not pdf_path.exists():
        print(f"ERROR: {pdf_path} not found")
        sys.exit(1)

    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Extracting from: {pdf_path}")
    print(f"Output to: {output_dir}")
    print()

    print("Extracting text...")
    page_stats = extract_text(pdf_path, output_dir)
    print(f"  {len(page_stats)} pages")

    print("Extracting tables...")
    table_stats = extract_tables(pdf_path, output_dir)
    print(f"  {len(table_stats)} tables")

    print("Extracting images...")
    image_stats = extract_images(pdf_path, output_dir)
    ok_images = [i for i in image_stats if "error" not in i]
    print(f"  {len(ok_images)} images ({len(image_stats) - len(ok_images)} failures)")

    print("\nWriting report...")
    write_report(output_dir, pdf_path.name, page_stats, table_stats, image_stats)

    print(f"\nDone. See {output_dir / 'extraction_report.md'}")


if __name__ == "__main__":
    main()
