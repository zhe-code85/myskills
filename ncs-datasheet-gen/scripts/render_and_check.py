#! python3
"""Render and scan datasheet PDF/text outputs for visual-check evidence."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


FIELD_CODE_PATTERNS = [
    re.compile(r"\bTOC\s+\\", re.IGNORECASE),
    re.compile(r"\bPAGEREF\b", re.IGNORECASE),
    re.compile(r"\bMERGEFORMAT\b", re.IGNORECASE),
]

BROKEN_DS_PATTERNS = [
    re.compile(r"D\s+S\s+_", re.IGNORECASE),
    re.compile(r"DS_[A-Z_]{2,}\.\.\."),
    re.compile(r"DS_NEED_CO\s+NFIRM", re.IGNORECASE),
    re.compile(r"DS_COMPETITO\.\.\.", re.IGNORECASE),
]


def read_text(path: Path | None) -> str:
    if not path:
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def extract_pdf_text(pdf: Path) -> str:
    try:
        import fitz  # type: ignore
    except Exception as exc:  # noqa: BLE001 - optional dependency.
        raise RuntimeError("PyMuPDF is required to extract text from PDF when --text is not provided") from exc

    doc = fitz.open(str(pdf))
    try:
        return "\n".join(page.get_text() for page in doc)
    finally:
        doc.close()


def render_pdf(pdf: Path, out_dir: Path, scale: float) -> tuple[list[str], list[int], str | None]:
    try:
        import fitz  # type: ignore
    except Exception:
        return [], [], "PyMuPDF not available; PDF rendering not run"

    image_dir = out_dir / "pages"
    image_dir.mkdir(parents=True, exist_ok=True)
    rendered: list[str] = []
    blank_pages: list[int] = []
    doc = fitz.open(str(pdf))
    try:
        matrix = fitz.Matrix(scale, scale)
        for index, page in enumerate(doc, start=1):
            pix = page.get_pixmap(matrix=matrix, alpha=False)
            image_path = image_dir / f"page_{index:02d}.png"
            pix.save(str(image_path))
            rendered.append(str(image_path))
            sample = pix.samples
            if sample:
                non_white = sum(1 for value in sample[:: max(1, len(sample) // 10000)] if value < 245)
                if non_white < 10:
                    blank_pages.append(index)
    finally:
        doc.close()
    return rendered, blank_pages, None


def find_pattern_lines(text: str, patterns: list[re.Pattern[str]]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        for pattern in patterns:
            match = pattern.search(line)
            if match:
                findings.append({"line": line_no, "pattern": pattern.pattern, "text": line.strip()[:240]})
                break
    return findings


def find_stale_terms(text: str, terms: list[str]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    folded_lines = text.splitlines()
    for term in terms:
        if not term:
            continue
        pattern = re.compile(re.escape(term), re.IGNORECASE)
        for line_no, line in enumerate(folded_lines, start=1):
            if pattern.search(line):
                findings.append({"line": line_no, "term": term, "text": line.strip()[:240]})
                break
    return findings


def build_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Visual Check Report",
        "",
        f"Status: {payload['status']}",
        "",
        "Inputs:",
    ]
    for key in ("pdf", "text"):
        if payload.get(key):
            lines.append(f"- {key}: `{payload[key]}`")
    lines.extend([
        f"- rendered pages: {len(payload.get('rendered_pages', []))}",
        "",
        "Findings:",
    ])
    findings = payload.get("findings", {})
    any_findings = False
    for label, rows in findings.items():
        if not rows:
            continue
        any_findings = True
        lines.append(f"- {label}: {len(rows)}")
        for row in rows[:10]:
            if isinstance(row, dict):
                detail = row.get("text") or row.get("term") or row
                lines.append(f"  - {detail}")
            else:
                lines.append(f"  - {row}")
    if not any_findings:
        lines.append("- none")
    if payload.get("render_warning"):
        lines.extend(["", f"Render warning: {payload['render_warning']}"])
    return "\n".join(lines) + "\n"


def make_payload(args: argparse.Namespace) -> dict[str, Any]:
    args.out_dir.mkdir(parents=True, exist_ok=True)
    text = read_text(args.text)
    if not text and args.pdf:
        text = extract_pdf_text(args.pdf)
        extracted_path = args.out_dir / "extracted-text.txt"
        extracted_path.write_text(text, encoding="utf-8")

    rendered_pages: list[str] = []
    blank_pages: list[int] = []
    render_warning = None
    if args.pdf:
        rendered_pages, blank_pages, render_warning = render_pdf(args.pdf, args.out_dir, args.scale)

    field_code_lines = find_pattern_lines(text, FIELD_CODE_PATTERNS)
    broken_ds_lines = find_pattern_lines(text, BROKEN_DS_PATTERNS)
    stale_terms = find_stale_terms(text, args.stale_term or [])
    findings = {
        "visible_field_codes": field_code_lines,
        "broken_ds_markings": broken_ds_lines,
        "stale_terms": stale_terms,
        "blank_pages": blank_pages,
    }
    status = "failed" if any(findings.values()) else "passed"
    return {
        "status": status,
        "pdf": str(args.pdf) if args.pdf else "",
        "text": str(args.text) if args.text else "",
        "rendered_pages": rendered_pages,
        "render_warning": render_warning,
        "findings": findings,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Render and scan datasheet PDF/text output.")
    parser.add_argument("--pdf", type=Path, help="PDF to render and scan")
    parser.add_argument("--text", type=Path, help="Extracted text file to scan")
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, help="visual-check.md output path")
    parser.add_argument("--stale-term", action="append", default=[], help="Term that must not appear in visible text")
    parser.add_argument("--scale", type=float, default=1.6, help="PDF render scale")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    args = parser.parse_args(argv)

    try:
        if not args.pdf and not args.text:
            raise ValueError("provide --pdf, --text, or both")
        payload = make_payload(args)
    except Exception as exc:  # noqa: BLE001 - CLI should report compact failures.
        payload = {"status": "failed", "errors": [str(exc)], "findings": {}}

    output_path = args.output or (args.out_dir / "visual-check.md")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(build_markdown(payload), encoding="utf-8")

    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"status: {payload['status']}")
        print(f"report: {output_path}")
    return 0 if payload["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
