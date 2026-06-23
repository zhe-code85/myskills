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
R = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"


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


def rel_attr(node: ET.Element, name: str) -> str | None:
    return node.attrib.get(R + name)


def local_name(node: ET.Element) -> str:
    return node.tag.rsplit("}", 1)[-1]


def child_attr(node: ET.Element, child_path: str, name: str) -> str | None:
    child = node.find(child_path, NS)
    if child is None:
        return None
    return attr(child, name)


def first_text_sample(text: str, limit: int = 180) -> str:
    normalized = " ".join(text.split())
    return normalized[:limit]


def part_text(package: zipfile.ZipFile, name: str) -> str:
    root = read_xml(package, name)
    if root is None:
        return ""
    return text_of(root)


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


def section_records(document: ET.Element | None) -> list[dict]:
    if document is None:
        return []
    records = []
    for index, section in enumerate(document.findall(".//w:sectPr", NS), start=1):
        pg_size = section.find("./w:pgSz", NS)
        pg_mar = section.find("./w:pgMar", NS)
        cols = section.find("./w:cols", NS)
        records.append(
            {
                "index": index,
                "page_size": {
                    "w": attr(pg_size, "w") if pg_size is not None else None,
                    "h": attr(pg_size, "h") if pg_size is not None else None,
                    "orient": attr(pg_size, "orient") if pg_size is not None else None,
                },
                "margins": {
                    key: attr(pg_mar, key) if pg_mar is not None else None
                    for key in ("top", "right", "bottom", "left", "header", "footer", "gutter")
                },
                "columns": {
                    "num": attr(cols, "num") if cols is not None else None,
                    "space": attr(cols, "space") if cols is not None else None,
                    "equal_width": attr(cols, "equalWidth") if cols is not None else None,
                },
                "header_refs": [
                    {"type": attr(ref, "type"), "r_id": rel_attr(ref, "id")}
                    for ref in section.findall("./w:headerReference", NS)
                ],
                "footer_refs": [
                    {"type": attr(ref, "type"), "r_id": rel_attr(ref, "id")}
                    for ref in section.findall("./w:footerReference", NS)
                ],
            }
        )
    return records


def paragraph_style_id(paragraph: ET.Element) -> str | None:
    p_style = paragraph.find("./w:pPr/w:pStyle", NS)
    return attr(p_style, "val") if p_style is not None else None


def table_record(table: ET.Element, index: int) -> dict:
    rows = table.findall("./w:tr", NS)
    grid_cols = [attr(col, "w") for col in table.findall("./w:tblGrid/w:gridCol", NS)]
    tbl_style = table.find("./w:tblPr/w:tblStyle", NS)
    header_shading = [
        attr(shd, "fill")
        for shd in (rows[0].findall(".//w:tcPr/w:shd", NS) if rows else [])
        if attr(shd, "fill")
    ]
    borders = table.findall("./w:tblPr/w:tblBorders/*", NS)
    return {
        "index": index,
        "row_count": len(rows),
        "max_cell_count": max((len(row.findall("./w:tc", NS)) for row in rows), default=0),
        "style_id": attr(tbl_style, "val") if tbl_style is not None else None,
        "grid_columns": grid_cols,
        "header_shading": sorted(set(header_shading)),
        "border_tags": sorted({local_name(border) for border in borders}),
        "text_sample": first_text_sample(text_of(table)),
    }


def body_block_records(document: ET.Element | None) -> tuple[list[dict], list[dict]]:
    if document is None:
        return [], []
    body = document.find(".//w:body", NS)
    if body is None:
        return [], []
    blocks: list[dict] = []
    notes: list[dict] = []
    table_index = 0
    paragraph_index = 0
    previous_block: dict | None = None
    for child in list(body):
        kind = local_name(child)
        if kind == "tbl":
            table_index += 1
            block = {"kind": "table", "table_index": table_index, "text_sample": first_text_sample(text_of(child))}
        elif kind == "p":
            paragraph_index += 1
            text = text_of(child).strip()
            block = {
                "kind": "paragraph",
                "paragraph_index": paragraph_index,
                "style_id": paragraph_style_id(child),
                "text_sample": first_text_sample(text),
            }
            if text.lower().startswith(("note", "notes")):
                notes.append(
                    {
                        "paragraph_index": paragraph_index,
                        "style_id": block["style_id"],
                        "text": text,
                        "previous_block": previous_block,
                    }
                )
        else:
            continue
        blocks.append(block)
        previous_block = block
    return blocks, notes


def page_role_candidates(body_text: str) -> list[dict]:
    rules = [
        ("front_page", ("DESCRIPTION", "FEATURES", "APPLICATIONS")),
        ("contents", ("CONTENTS",)),
        ("order_information", ("ORDER INFORMATION", "DEVICE INFORMATION")),
        ("pin_configuration", ("PIN CONFIGURATION", "PIN DESCRIPTION")),
        ("electrical_tables", ("ELECTRICAL CHARACTERISTICS", "ABSOLUTE MAXIMUM", "RECOMMENDED OPERATING")),
        ("application_figures", ("TYPICAL APPLICATION", "APPLICATION INFORMATION")),
        ("notice_footer", ("IMPORTANT NOTICE",)),
    ]
    upper_text = body_text.upper()
    candidates = []
    for role, markers in rules:
        found = [marker for marker in markers if marker in upper_text]
        if found:
            candidates.append({"role": role, "markers": found})
    return candidates


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
            style_id = paragraph_style_id(paragraph)
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
        body_blocks, note_records = body_block_records(document)
        sections = section_records(document)
        table_records = [table_record(table, index) for index, table in enumerate(tables, start=1)]
        header_parts = sorted(name for name in names if name.startswith("word/header"))
        footer_parts = sorted(name for name in names if name.startswith("word/footer"))
        header_footer_text = {
            name: first_text_sample(part_text(package, name), 500)
            for name in header_parts + footer_parts
        }
        document_text = text_of(document) if document is not None else ""
        layout_contract = {
            "kind": "layout_contract",
            "source": "structured_docx",
            "page_setup": {
                "section_count": len(sections),
                "two_column_section_count": len(two_cols),
                "column_break_count": len(column_breaks),
                "sections": sections,
            },
            "header_footer": {
                "header_parts": header_parts,
                "footer_parts": footer_parts,
                "text_by_part": header_footer_text,
            },
            "tables": table_records,
            "notes": note_records,
            "page_role_candidates": page_role_candidates(document_text),
            "body_block_sample": body_blocks[:80],
            "rendering_observations_required": [
                "page_region_boundaries",
                "left_right_or_top_bottom_layout",
                "divider_lines_and_rule_positions",
                "header_footer_visual_boundaries",
                "notes_position_relative_to_table_or_figure",
                "figure_text_relative_position",
                "watermark_rendering",
                "font_substitution_or_line_visibility_mismatches",
            ],
        }

        return {
            "type": "docx",
            "path": str(path),
            "paragraph_count": len(paragraphs),
            "table_count": len(tables),
            "drawing_count": len(drawings),
            "column_break_count": len(column_breaks),
            "two_column_section_count": len(two_cols),
            "section_count": len(sections),
            "sections": sections,
            "style_ids": sorted(style_ids),
            "style_names": style_names,
            "paragraph_styles": paragraph_styles,
            "numbering_ids": num_ids,
            "note_paragraphs": note_paragraphs,
            "note_records": note_records,
            "comment_count": len(comment_texts),
            "comments": comment_texts,
            "comment_guidance": comment_guidance,
            "media": sorted(name for name in names if name.startswith("word/media/")),
            "headers": header_parts,
            "footers": footer_parts,
            "header_footer_text": header_footer_text,
            "table_records": table_records,
            "layout_contract": layout_contract,
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
            "layout_contract_page_roles_sections_boundaries",
            "heading_style_ids_spacing_case",
            "list_numbering_indents_symbols",
            "contents_toc_tabs_page_numbers_exclusions",
            "notes_after_tables",
            "table_borders_fonts_header_shading",
            "image_positions_captions_source_labels",
            "rendering_observations_boundaries_divider_lines_notes_positions",
            "template_comments_applicability",
        ],
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote analysis report: {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
