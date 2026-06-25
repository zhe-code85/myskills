#! python3
"""Check whether a generated DOCX preserves key template layout structures."""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
import zipfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET


W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
NS = {"w": W_NS, "rel": REL_NS}


@dataclass
class DocxStructure:
    path: str
    zip_entries: int
    sections: int
    paragraphs: int
    tables: int
    drawings: int
    legacy_pictures: int
    document_header_refs: int
    document_footer_refs: int
    rel_header_count: int
    rel_footer_count: int
    header_parts: int
    footer_parts: int
    media_parts: int
    chart_parts: int
    embedding_parts: int
    comments: int
    content_controls: int
    toc_fields: int
    field_chars: int
    styles: int


def normalize_resource_label(value: str) -> str:
    value = value.lower()
    value = re.sub(r"[_\-]+", " ", value)
    value = re.sub(r"\b(count|objects|object|parts|part)\b", "", value)
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def load_asset_diff(path: Path | None) -> dict[str, dict[str, Any]]:
    if not path:
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict):
        entries = data.get("accepted_reductions", data.get("reductions", []))
    elif isinstance(data, list):
        entries = data
    else:
        raise ValueError("asset diff must be a JSON object or list")

    accepted: dict[str, dict[str, Any]] = {}
    for item in entries:
        if not isinstance(item, dict):
            continue
        resource = str(item.get("resource", "")).strip()
        reason = str(item.get("reason", "")).strip()
        status = str(item.get("status", "")).strip().lower()
        if not resource or not reason:
            continue
        if status not in {"accepted", "accepted-with-notes", "intentional", "planned"}:
            continue
        accepted[normalize_resource_label(resource)] = item
    return accepted


def find_accepted_reduction(accepted: dict[str, dict[str, Any]], label: str) -> dict[str, Any] | None:
    normalized = normalize_resource_label(label)
    if normalized in accepted:
        return accepted[normalized]
    for key, item in accepted.items():
        if normalized in key or key in normalized:
            return item
    return None


def read_part(package: zipfile.ZipFile, name: str) -> bytes:
    try:
        return package.read(name)
    except KeyError:
        return b""


def parse_xml(raw: bytes, name: str) -> ET.Element:
    if not raw:
        raise ValueError(f"{name} is missing")
    try:
        return ET.fromstring(raw)
    except ET.ParseError as exc:
        raise ValueError(f"{name} is not valid XML: {exc}") from exc


def count_relationships(root: ET.Element, relationship_type: str) -> int:
    return sum(1 for rel in root if relationship_type in rel.attrib.get("Type", ""))


def count_package_parts(names: set[str], pattern: str) -> int:
    return sum(1 for name in names if re.fullmatch(pattern, name))


def summarize_docx(path: Path) -> DocxStructure:
    if not path.exists():
        raise FileNotFoundError(path)

    with zipfile.ZipFile(path) as package:
        names = set(package.namelist())
        document = parse_xml(read_part(package, "word/document.xml"), "word/document.xml")
        rels_raw = read_part(package, "word/_rels/document.xml.rels")
        rels = parse_xml(rels_raw, "word/_rels/document.xml.rels") if rels_raw else ET.Element("Relationships")
        styles_raw = read_part(package, "word/styles.xml")
        styles = parse_xml(styles_raw, "word/styles.xml") if styles_raw else ET.Element("styles")
        comments_raw = read_part(package, "word/comments.xml")
        comments = parse_xml(comments_raw, "word/comments.xml") if comments_raw else ET.Element("comments")

        toc_fields = 0
        for instr_text in document.findall(".//w:instrText", NS):
            if instr_text.text and "TOC" in instr_text.text:
                toc_fields += 1

        return DocxStructure(
            path=str(path),
            zip_entries=len(names),
            sections=len(document.findall(".//w:sectPr", NS)),
            paragraphs=len(document.findall(".//w:p", NS)),
            tables=len(document.findall(".//w:tbl", NS)),
            drawings=len(document.findall(".//w:drawing", NS)),
            legacy_pictures=len(document.findall(".//w:pict", NS)),
            document_header_refs=len(document.findall(".//w:sectPr/w:headerReference", NS)),
            document_footer_refs=len(document.findall(".//w:sectPr/w:footerReference", NS)),
            rel_header_count=count_relationships(rels, "/header"),
            rel_footer_count=count_relationships(rels, "/footer"),
            header_parts=count_package_parts(names, r"word/header\d+\.xml"),
            footer_parts=count_package_parts(names, r"word/footer\d+\.xml"),
            media_parts=count_package_parts(names, r"word/media/.+"),
            chart_parts=count_package_parts(names, r"word/charts/.+"),
            embedding_parts=count_package_parts(names, r"word/embeddings/.+"),
            comments=len(comments.findall(".//w:comment", NS)),
            content_controls=len(document.findall(".//w:sdt", NS)),
            toc_fields=toc_fields,
            field_chars=len(document.findall(".//w:fldChar", NS)),
            styles=len(styles.findall(".//w:style", NS)),
        )


def min_expected_count(expected: int, ratio: float) -> int:
    if expected <= 0 or ratio <= 0:
        return 0
    return max(1, math.ceil(expected * ratio))


def append_ratio_check(
    *,
    label: str,
    expected: int,
    actual: int,
    ratio: float,
    errors: list[str],
    warnings: list[str],
    accepted_reductions: dict[str, dict[str, Any]],
    accepted_notes: list[dict[str, Any]],
    severity: str = "error",
) -> None:
    minimum = min_expected_count(expected, ratio)
    if minimum and actual < minimum:
        message = f"{label} collapsed: template has {expected}, output has {actual}, minimum expected {minimum}"
        accepted = find_accepted_reduction(accepted_reductions, label)
        if accepted:
            reason = str(accepted.get("reason", "")).strip()
            warnings.append(f"{message}; accepted reduction: {reason}")
            accepted_notes.append({"label": label, "template": expected, "output": actual, "reason": reason})
            return
        if severity == "warning":
            warnings.append(message)
        else:
            errors.append(message)


def compare_structures(
    template: DocxStructure,
    output: DocxStructure,
    *,
    min_section_ratio: float,
    min_zip_entry_ratio: float,
    min_paragraph_ratio: float,
    min_table_ratio: float,
    min_drawing_ratio: float,
    min_media_ratio: float,
    min_chart_ratio: float,
    min_embedding_ratio: float,
    min_legacy_picture_ratio: float,
    accepted_reductions: dict[str, dict[str, Any]],
) -> tuple[list[str], list[str], list[dict[str, Any]]]:
    errors: list[str] = []
    warnings: list[str] = []
    accepted_notes: list[dict[str, Any]] = []

    min_sections = min_expected_count(template.sections, min_section_ratio)
    if output.sections < min_sections:
        errors.append(
            f"section count collapsed: template has {template.sections}, output has {output.sections}, minimum expected {min_sections}"
        )

    checks = [
        ("header references", "header", template.document_header_refs, output.document_header_refs),
        ("footer references", "footer", template.document_footer_refs, output.document_footer_refs),
        ("header relationships", "header", template.rel_header_count, output.rel_header_count),
        ("footer relationships", "footer", template.rel_footer_count, output.rel_footer_count),
        ("header parts", "header", template.header_parts, output.header_parts),
        ("footer parts", "footer", template.footer_parts, output.footer_parts),
    ]
    for label, token, expected, actual in checks:
        if expected and actual < expected:
            errors.append(f"{label} lost: template {token} count is {expected}, output count is {actual}")

    if template.toc_fields and output.toc_fields < template.toc_fields:
        errors.append(f"TOC field lost: template has {template.toc_fields}, output has {output.toc_fields}")

    if template.field_chars and output.field_chars < template.field_chars:
        warnings.append(f"field codes reduced: template has {template.field_chars}, output has {output.field_chars}")

    if template.styles and output.styles < template.styles:
        warnings.append(f"styles reduced: template has {template.styles}, output has {output.styles}")

    append_ratio_check(
        label="DOCX package entries",
        expected=template.zip_entries,
        actual=output.zip_entries,
        ratio=min_zip_entry_ratio,
        errors=errors,
        warnings=warnings,
        accepted_reductions=accepted_reductions,
        accepted_notes=accepted_notes,
    )
    append_ratio_check(
        label="paragraph count",
        expected=template.paragraphs,
        actual=output.paragraphs,
        ratio=min_paragraph_ratio,
        errors=errors,
        warnings=warnings,
        accepted_reductions=accepted_reductions,
        accepted_notes=accepted_notes,
        severity="warning",
    )
    append_ratio_check(
        label="table count",
        expected=template.tables,
        actual=output.tables,
        ratio=min_table_ratio,
        errors=errors,
        warnings=warnings,
        accepted_reductions=accepted_reductions,
        accepted_notes=accepted_notes,
        severity="warning",
    )
    append_ratio_check(
        label="drawing objects",
        expected=template.drawings,
        actual=output.drawings,
        ratio=min_drawing_ratio,
        errors=errors,
        warnings=warnings,
        accepted_reductions=accepted_reductions,
        accepted_notes=accepted_notes,
    )
    append_ratio_check(
        label="legacy pictures",
        expected=template.legacy_pictures,
        actual=output.legacy_pictures,
        ratio=min_legacy_picture_ratio,
        errors=errors,
        warnings=warnings,
        accepted_reductions=accepted_reductions,
        accepted_notes=accepted_notes,
    )
    append_ratio_check(
        label="media parts",
        expected=template.media_parts,
        actual=output.media_parts,
        ratio=min_media_ratio,
        errors=errors,
        warnings=warnings,
        accepted_reductions=accepted_reductions,
        accepted_notes=accepted_notes,
    )
    append_ratio_check(
        label="chart parts",
        expected=template.chart_parts,
        actual=output.chart_parts,
        ratio=min_chart_ratio,
        errors=errors,
        warnings=warnings,
        accepted_reductions=accepted_reductions,
        accepted_notes=accepted_notes,
    )
    append_ratio_check(
        label="embedded object parts",
        expected=template.embedding_parts,
        actual=output.embedding_parts,
        ratio=min_embedding_ratio,
        errors=errors,
        warnings=warnings,
        accepted_reductions=accepted_reductions,
        accepted_notes=accepted_notes,
    )
    if template.comments and output.comments < template.comments:
        accepted = find_accepted_reduction(accepted_reductions, "template comments")
        message = f"template comments reduced: template has {template.comments}, output has {output.comments}"
        if accepted:
            reason = str(accepted.get("reason", "")).strip()
            warnings.append(f"{message}; accepted reduction: {reason}")
            accepted_notes.append(
                {"label": "template comments", "template": template.comments, "output": output.comments, "reason": reason}
            )
        else:
            warnings.append(message)

    return errors, warnings, accepted_notes


def make_payload(args: argparse.Namespace) -> dict[str, Any]:
    template_path = args.template
    output_path = args.output
    template = summarize_docx(template_path)
    output = summarize_docx(output_path)
    accepted_reductions = load_asset_diff(args.asset_diff)
    errors, warnings, accepted_notes = compare_structures(
        template,
        output,
        min_section_ratio=args.min_section_ratio,
        min_zip_entry_ratio=args.min_zip_entry_ratio,
        min_paragraph_ratio=args.min_paragraph_ratio,
        min_table_ratio=args.min_table_ratio,
        min_drawing_ratio=args.min_drawing_ratio,
        min_media_ratio=args.min_media_ratio,
        min_chart_ratio=args.min_chart_ratio,
        min_embedding_ratio=args.min_embedding_ratio,
        min_legacy_picture_ratio=args.min_legacy_picture_ratio,
        accepted_reductions=accepted_reductions,
    )
    status = "failed" if errors else ("accepted-with-notes" if accepted_notes else "passed")
    return {
        "status": status,
        "template": asdict(template),
        "output": asdict(output),
        "errors": errors,
        "warnings": warnings,
        "accepted_reductions": accepted_notes,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check generated DOCX template layout fidelity.")
    parser.add_argument("--template", type=Path, required=True, help="Source template DOCX")
    parser.add_argument("--output", type=Path, required=True, help="Generated output DOCX")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")
    parser.add_argument(
        "--min-section-ratio",
        type=float,
        default=1.0,
        help="Minimum output/template section count ratio. Default requires preserving section count.",
    )
    parser.add_argument("--min-zip-entry-ratio", type=float, default=0.40, help="Minimum package-entry retention ratio.")
    parser.add_argument("--min-paragraph-ratio", type=float, default=0.40, help="Minimum paragraph retention ratio.")
    parser.add_argument("--min-table-ratio", type=float, default=0.50, help="Minimum table retention ratio.")
    parser.add_argument("--min-drawing-ratio", type=float, default=0.50, help="Minimum drawing-object retention ratio.")
    parser.add_argument("--min-legacy-picture-ratio", type=float, default=0.50, help="Minimum VML picture retention ratio.")
    parser.add_argument("--min-media-ratio", type=float, default=0.50, help="Minimum media-part retention ratio.")
    parser.add_argument("--min-chart-ratio", type=float, default=0.50, help="Minimum chart-part retention ratio.")
    parser.add_argument("--min-embedding-ratio", type=float, default=0.50, help="Minimum embedded-object retention ratio.")
    parser.add_argument("--asset-diff", type=Path, help="JSON file documenting intentional asset reductions.")
    args = parser.parse_args(argv)

    try:
        payload = make_payload(args)
    except Exception as exc:  # noqa: BLE001 - command line should report structural failures cleanly.
        payload = {
            "status": "failed",
            "template": str(args.template),
            "output": str(args.output),
            "errors": [str(exc)],
            "warnings": [],
        }

    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"status: {payload['status']}")
        for message in payload.get("errors", []):
            print(f"error: {message}")
        for message in payload.get("warnings", []):
            print(f"warning: {message}")

    return 0 if payload["status"] in {"passed", "accepted-with-notes"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
