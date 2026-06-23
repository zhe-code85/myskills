"""Analyze datasheet source documents and emit a reusable JSON fact report."""

from __future__ import annotations

import argparse
import json
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET


NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def read_xml(package: zipfile.ZipFile, name: str) -> ET.Element | None:
    if name not in package.namelist():
        return None
    try:
        return ET.fromstring(package.read(name))
    except ET.ParseError:
        return None


def text_of(node: ET.Element) -> str:
    return "".join(text.text or "" for text in node.findall(".//w:t", NS))


def attr(node: ET.Element, name: str) -> str | None:
    return node.attrib.get(W + name)


def comment_anchor_texts(document: ET.Element | None) -> dict[str, str]:
    if document is None:
        return {}
    anchors: dict[str, str] = {}
    for paragraph in document.findall(".//w:p", NS):
        ids: set[str] = set()
        for tag in ("commentRangeStart", "commentRangeEnd", "commentReference"):
            for marker in paragraph.findall(f".//w:{tag}", NS):
                comment_id = attr(marker, "id")
                if comment_id:
                    ids.add(comment_id)
        if not ids:
            continue
        text = text_of(paragraph).strip()
        for comment_id in ids:
            anchors.setdefault(comment_id, text)
    return anchors


def comment_guidance_records(comments: ET.Element | None, document: ET.Element | None, path: Path) -> list[dict]:
    if comments is None:
        return []
    anchors = comment_anchor_texts(document)
    guidance = []
    for comment in comments.findall(".//w:comment", NS):
        comment_id = attr(comment, "id") or ""
        instruction = text_of(comment).strip()
        if not instruction:
            continue
        guidance.append(
            {
                "id": f"template_comment_{comment_id}" if comment_id else "template_comment",
                "kind": "template_guidance",
                "source_ref": f"{path.name} comment {comment_id}".strip(),
                "comment_id": comment_id,
                "author": attr(comment, "author") or "",
                "date": attr(comment, "date") or "",
                "instruction": instruction,
                "anchor_text": anchors.get(comment_id, ""),
                "disposition_required": True,
                "decision": "<applied|not_applicable|needs_clarification>",
                "evidence": "<how this guidance was applied or why it does not apply>",
            }
        )
    return guidance


def analyze_docx(path: Path) -> dict:
    with zipfile.ZipFile(path) as package:
        names = package.namelist()
        document = read_xml(package, "word/document.xml")
        styles = read_xml(package, "word/styles.xml")
        numbering = read_xml(package, "word/numbering.xml")
        comments = read_xml(package, "word/comments.xml")

        paragraphs = document.findall(".//w:p", NS) if document is not None else []
        tables = document.findall(".//w:tbl", NS) if document is not None else []
        drawings = document.findall(".//w:drawing", NS) if document is not None else []
        column_breaks = document.findall(".//w:br[@w:type='column']", NS) if document is not None else []
        two_cols = document.findall(".//w:cols[@w:num='2']", NS) if document is not None else []

        style_ids: list[str] = []
        style_names: dict[str, str] = {}
        if styles is not None:
            for style in styles.findall(".//w:style", NS):
                style_id = attr(style, "styleId")
                if style_id:
                    style_ids.append(style_id)
                    name = style.find("./w:name", NS)
                    if name is not None and attr(name, "val"):
                        style_names[style_id] = attr(name, "val") or ""

        paragraph_styles: dict[str, int] = {}
        note_paragraphs: list[str] = []
        for paragraph in paragraphs:
            p_style = paragraph.find("./w:pPr/w:pStyle", NS)
            style_id = attr(p_style, "val") if p_style is not None else None
            if style_id:
                paragraph_styles[style_id] = paragraph_styles.get(style_id, 0) + 1
            text = text_of(paragraph).strip()
            if text.lower().startswith(("note", "notes")):
                note_paragraphs.append(text)

        num_ids: dict[str, int] = {}
        if document is not None:
            for num_id in document.findall(".//w:numPr/w:numId", NS):
                value = attr(num_id, "val")
                if value:
                    num_ids[value] = num_ids.get(value, 0) + 1

        comment_guidance = comment_guidance_records(comments, document, path)
        comment_texts = [item["instruction"] for item in comment_guidance]

        return {
            "type": "docx",
            "path": str(path),
            "paragraph_count": len(paragraphs),
            "table_count": len(tables),
            "drawing_count": len(drawings),
            "column_break_count": len(column_breaks),
            "two_column_section_count": len(two_cols),
            "style_ids": sorted(style_ids),
            "style_names": style_names,
            "paragraph_styles": paragraph_styles,
            "numbering_ids": num_ids,
            "note_paragraphs": note_paragraphs,
            "comment_count": len(comment_texts),
            "comments": comment_texts,
            "comment_guidance": comment_guidance,
            "media": sorted(name for name in names if name.startswith("word/media/")),
            "headers": sorted(name for name in names if name.startswith("word/header")),
            "footers": sorted(name for name in names if name.startswith("word/footer")),
            "has_numbering": numbering is not None,
        }


def analyze_pdf(path: Path) -> dict:
    result = {"type": "pdf", "path": str(path), "page_count": None, "text_sample": ""}
    try:
        import fitz  # type: ignore
    except Exception as exc:
        result["warning"] = f"PyMuPDF unavailable: {exc}"
        return result
    with fitz.open(path) as pdf:
        result["page_count"] = pdf.page_count
        if pdf.page_count:
            result["text_sample"] = pdf[0].get_text("text")[:2000]
    return result


def analyze_path(path: Path) -> dict:
    if not path.exists():
        return {"type": "missing", "path": str(path)}
    suffix = path.suffix.lower()
    if suffix in {".docx", ".docm", ".dotx", ".dotm"}:
        return {"docx": analyze_docx(path)}
    if suffix == ".pdf":
        return {"pdf": analyze_pdf(path)}
    return {"type": "unsupported", "path": str(path), "suffix": path.suffix}


def role_path(value: str) -> tuple[str, Path]:
    if "=" not in value:
        raise argparse.ArgumentTypeError("expected role=path")
    role, path = value.split("=", 1)
    role = role.strip()
    if not role:
        raise argparse.ArgumentTypeError("source role must not be empty")
    if not path.strip():
        raise argparse.ArgumentTypeError("source path must not be empty")
    return role, Path(path)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Analyze role-labeled DOCX/PDF datasheet source documents.")
    parser.add_argument(
        "--source",
        action="append",
        type=role_path,
        help="Role-labeled source as role=path; repeatable, e.g. style_template=template.docx",
    )
    parser.add_argument("--template", type=Path, help="Legacy alias for --source style_template=PATH")
    parser.add_argument("--competitor", type=Path, help="Legacy alias for --source reference_datasheet=PATH")
    parser.add_argument("--company", type=Path, help="Legacy alias for --source company_prior_datasheet=PATH")
    parser.add_argument("--out", type=Path, required=True, help="Output JSON report")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    documents: dict[str, dict] = {}
    for role, path in args.source or []:
        documents[role] = analyze_path(path)
    legacy_sources = {
        "style_template": args.template,
        "reference_datasheet": args.competitor,
        "company_prior_datasheet": args.company,
    }
    for role, path in legacy_sources.items():
        if path:
            documents[role] = analyze_path(path)
    if not documents:
        print("ERROR: pass at least one --source role=path or legacy source path", file=sys.stderr)
        return 2
    report = {
        "documents": documents,
        "source_map_guidance": [
            "Assign a stable fact id to each extracted claim, table, figure, or layout fact.",
            "Record source_role, source_path, page/section/table reference, confidence, and risk status.",
            "Convert DOCX comment_guidance into source_map template_guidance items with required dispositions.",
            "Do not promote reference-derived or competitor-derived values to confirmed target claims.",
        ],
        "format_fact_checklist": [
            "front_page_sections_headers_footers_watermark",
            "heading_style_ids_spacing_case",
            "list_numbering_indents_symbols",
            "contents_toc_tabs_page_numbers_exclusions",
            "notes_after_tables",
            "table_borders_fonts_header_shading",
            "image_positions_captions_source_labels",
            "template_comments_applicability",
        ],
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote analysis report: {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
