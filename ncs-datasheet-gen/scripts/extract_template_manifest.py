#! python3
"""Extract a reusable DOCX template manifest for ncs-datasheet-gen."""

from __future__ import annotations

import argparse
import json
import re
import zipfile
from pathlib import Path
from typing import Any

from lxml import etree as ET

from check_docx_template_fidelity import summarize_docx


W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
NS = {"w": W_NS, "r": R_NS}


def w_tag(name: str) -> str:
    return f"{{{W_NS}}}{name}"


def text_of(element: ET.Element) -> str:
    return re.sub(r"\s+", " ", "".join(element.xpath(".//w:t/text()", namespaces=NS))).strip()


def slug(value: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9]+", "_", value.strip().lower()).strip("_")
    return value or "anchor"


def normalized_text(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def is_toc_like_heading(text: str) -> bool:
    folded = normalized_text(text)
    if "example" in folded:
        return False
    section_tokens = (
        "description",
        "features",
        "applications",
        "pin configuration",
        "pin description",
        "order information",
        "device information",
        "absolute maximum",
        "recommended operating",
        "thermal performance",
        "electrical characteristics",
        "functional description",
        "application information",
        "block diagram",
        "typical application",
        "typical performance",
        "package",
        "important notice",
        "revision history",
    )
    return bool(re.search(r"\d+$", re.sub(r"\s+", "", text))) and any(token in folded for token in section_tokens)


def is_heading_text(text: str) -> bool:
    if not text or len(text) > 90:
        return False
    if is_toc_like_heading(text):
        return False
    known = (
        "description",
        "features",
        "applications",
        "pin configuration",
        "pin description",
        "order information",
        "device information",
        "absolute maximum",
        "recommended operating",
        "thermal performance",
        "electrical characteristics",
        "functional description",
        "application information",
        "block diagram",
        "typical application",
        "typical performance",
        "package",
        "important notice",
        "revision history",
    )
    folded = normalized_text(text)
    if any(token in folded for token in known):
        return True
    letters = [char for char in text if char.isalpha()]
    if len(letters) < 3:
        return False
    return sum(1 for char in letters if char.isupper()) / len(letters) > 0.75


def read_xml(package: zipfile.ZipFile, name: str) -> ET.Element | None:
    try:
        return ET.fromstring(package.read(name))
    except KeyError:
        return None


def table_shape(table: ET.Element) -> tuple[int, int]:
    rows = table.findall("w:tr", NS)
    col_count = 0
    for row in rows:
        col_count = max(col_count, len(row.findall("w:tc", NS)))
    return len(rows), col_count


def extract_comments(package: zipfile.ZipFile) -> list[dict[str, Any]]:
    comments = read_xml(package, "word/comments.xml")
    if comments is None:
        return []
    rows: list[dict[str, Any]] = []
    for item in comments.findall("w:comment", NS):
        rows.append({
            "id": item.get(w_tag("id")),
            "author": item.get(w_tag("author"), ""),
            "text": text_of(item),
        })
    return rows


def infer_page_roles(anchor_keys: set[str], toc_fields: list[dict[str, Any]]) -> list[str]:
    roles: list[str] = []
    if anchor_keys:
        roles.append("cover_or_front_matter")
    if toc_fields:
        roles.append("toc")
    checks = [
        ("ordinary_body", {"description", "features", "applications"}),
        ("parameter_table", {"electrical_characteristics", "absolute_maximum_rating", "recommended_operating_conditions"}),
        ("pin_configuration", {"pin_configuration", "pin_description"}),
        ("figure_mixed_content", {"typical_application", "block_diagram", "typical_performance_characteristics"}),
        ("package_mechanical", {"package", "mechanical", "tape_reel", "tape_and_reel"}),
        ("legal_notice", {"important_notice", "legal", "support"}),
    ]
    for role, keys in checks:
        if any(any(key in anchor for key in keys) for anchor in anchor_keys):
            roles.append(role)
    return roles or ["unknown"]


def build_manifest(template: Path) -> dict[str, Any]:
    summary = summarize_docx(template)
    with zipfile.ZipFile(template) as package:
        document = read_xml(package, "word/document.xml")
        if document is None:
            raise ValueError("word/document.xml is missing")
        body = document.find("w:body", NS)
        if body is None:
            raise ValueError("word/document.xml has no w:body")

        paragraphs: list[dict[str, Any]] = []
        tables: list[dict[str, Any]] = []
        body_sequence: list[dict[str, Any]] = []
        anchors: dict[str, dict[str, Any]] = {}
        toc_fields: list[dict[str, Any]] = []
        protected_blocks: list[dict[str, Any]] = []
        p_index = 0
        t_index = 0

        for child_index, child in enumerate(body):
            if child.tag == w_tag("p"):
                text = text_of(child)
                has_field = bool(child.findall(".//w:fldChar", NS) or child.findall(".//w:instrText", NS))
                has_drawing = child.find(".//w:drawing", NS) is not None
                has_pict = child.find(".//w:pict", NS) is not None
                has_object = child.find(".//w:object", NS) is not None
                info = {
                    "index": p_index,
                    "child_index": child_index,
                    "text": text,
                    "has_field": has_field,
                    "has_drawing": has_drawing,
                    "has_legacy_picture": has_pict,
                    "has_ole_object": has_object,
                }
                paragraphs.append(info)
                body_sequence.append({"kind": "paragraph", "index": p_index, "child_index": child_index, "text": text})
                for instr in child.findall(".//w:instrText", NS):
                    if instr.text and "TOC" in instr.text:
                        toc_fields.append({"paragraph_index": p_index, "instruction": instr.text.strip()})
                if has_field:
                    protected_blocks.append({"kind": "paragraph", "index": p_index, "reason": "contains Word field"})
                if not has_field and is_heading_text(text):
                    key = slug(text)
                    suffix = 2
                    unique_key = key
                    while unique_key in anchors:
                        unique_key = f"{key}_{suffix}"
                        suffix += 1
                    anchors[unique_key] = {"paragraph_index": p_index, "text": text, "child_index": child_index}
                p_index += 1
            elif child.tag == w_tag("tbl"):
                rows, cols = table_shape(child)
                text = text_of(child)
                info = {
                    "index": t_index,
                    "child_index": child_index,
                    "rows": rows,
                    "cols": cols,
                    "preview": text[:300],
                    "header": text_of(child.find("w:tr", NS)) if child.find("w:tr", NS) is not None else "",
                }
                tables.append(info)
                body_sequence.append({"kind": "table", "index": t_index, "child_index": child_index, "text": text[:300]})
                t_index += 1

        replaceable_blocks = []
        for key, anchor in anchors.items():
            text = anchor["text"].lower()
            if any(token in text for token in ("description", "features", "applications", "pin", "electrical", "thermal", "package", "typical", "block", "order", "device")):
                replaceable_blocks.append({
                    "slot": key,
                    "anchor": key,
                    "paragraph_index": anchor["paragraph_index"],
                    "text": anchor["text"],
                })

        comments = extract_comments(package)

    inventory = {
        "package_entries": summary.zip_entries,
        "media_parts": summary.media_parts,
        "drawing_objects": summary.drawings,
        "legacy_pictures": summary.legacy_pictures,
        "chart_parts": summary.chart_parts,
        "embedding_parts": summary.embedding_parts,
        "comments": summary.comments,
        "sections": summary.sections,
        "tables": summary.tables,
        "paragraphs": summary.paragraphs,
        "toc_fields": summary.toc_fields,
        "field_chars": summary.field_chars,
        "styles": summary.styles,
    }
    return {
        "template": str(template),
        "sections": [{"index": index} for index in range(summary.sections)],
        "headers_footers": {
            "document_header_refs": summary.document_header_refs,
            "document_footer_refs": summary.document_footer_refs,
            "header_parts": summary.header_parts,
            "footer_parts": summary.footer_parts,
        },
        "toc_fields": toc_fields,
        "page_roles": infer_page_roles(set(anchors), toc_fields),
        "replaceable_blocks": replaceable_blocks,
        "anchors": anchors,
        "sample_rows": [{"table_index": table["index"], "header": table["header"], "rows": table["rows"], "cols": table["cols"]} for table in tables],
        "protected_blocks": protected_blocks,
        "resource_inventory": inventory,
        "comments": comments,
        "body": body_sequence,
        "paragraphs": paragraphs,
        "tables": tables,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Extract DOCX template manifest for ncs-datasheet-gen.")
    parser.add_argument("--template", type=Path, required=True, help="Input template DOCX")
    parser.add_argument("--output", type=Path, required=True, help="Output manifest JSON")
    args = parser.parse_args(argv)

    try:
        manifest = build_manifest(args.template)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        payload = {
            "status": "written",
            "template": str(args.template),
            "output": str(args.output),
            "anchors": len(manifest["anchors"]),
            "comments": len(manifest["comments"]),
        }
    except Exception as exc:  # noqa: BLE001 - CLI should report compact failures.
        payload = {"status": "failed", "errors": [str(exc)]}
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["status"] == "written" else 1


if __name__ == "__main__":
    raise SystemExit(main())
