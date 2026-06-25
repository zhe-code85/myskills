#! python3
"""Remove Word comments from a DOCX package while preserving other parts."""

from __future__ import annotations

import argparse
import json
import re
import zipfile
from pathlib import Path

from lxml import etree as ET


COMMENT_PARTS = {
    "word/comments.xml",
    "word/commentsExtended.xml",
    "word/commentsIds.xml",
    "word/commentsExtensible.xml",
}


def strip_comment_markup(raw: bytes) -> tuple[bytes, int]:
    parser = ET.XMLParser(resolve_entities=False, remove_blank_text=False)
    root = ET.fromstring(raw, parser)
    count = 0
    for element in list(root.iter()):
        name = ET.QName(element).localname
        if name not in {"commentRangeStart", "commentRangeEnd", "commentReference"}:
            continue
        parent = element.getparent()
        if parent is not None:
            parent.remove(element)
            count += 1
    return ET.tostring(root, encoding="UTF-8", xml_declaration=True), count


def strip_rels(raw: bytes) -> tuple[bytes, int]:
    parser = ET.XMLParser(resolve_entities=False, remove_blank_text=False)
    root = ET.fromstring(raw, parser)
    count = 0
    for rel in list(root):
        rel_type = rel.get("Type", "").lower()
        target = rel.get("Target", "").lower()
        if "comments" in rel_type or "comments" in target:
            root.remove(rel)
            count += 1
    return ET.tostring(root, encoding="UTF-8", xml_declaration=True), count


def strip_content_types(raw: bytes) -> tuple[bytes, int]:
    parser = ET.XMLParser(resolve_entities=False, remove_blank_text=False)
    root = ET.fromstring(raw, parser)
    count = 0
    for node in list(root):
        if "comments" in node.get("PartName", "").lower():
            root.remove(node)
            count += 1
    return ET.tostring(root, encoding="UTF-8", xml_declaration=True), count


def strip_comments(input_docx: Path, output_docx: Path) -> dict[str, object]:
    output_docx.parent.mkdir(parents=True, exist_ok=True)
    removed_parts: list[str] = []
    markup_removed = 0
    rels_removed = 0
    content_types_removed = 0
    with zipfile.ZipFile(input_docx, "r") as src, zipfile.ZipFile(output_docx, "w", zipfile.ZIP_DEFLATED) as dst:
        for info in src.infolist():
            if info.filename in COMMENT_PARTS:
                removed_parts.append(info.filename)
                continue
            raw = src.read(info.filename)
            if info.filename.startswith("word/") and info.filename.endswith(".xml"):
                raw, count = strip_comment_markup(raw)
                markup_removed += count
            elif info.filename.endswith(".rels"):
                raw, count = strip_rels(raw)
                rels_removed += count
            elif info.filename == "[Content_Types].xml":
                raw, count = strip_content_types(raw)
                content_types_removed += count
            dst.writestr(info, raw)
    return {
        "status": "stripped",
        "input": str(input_docx),
        "output": str(output_docx),
        "removed_parts": removed_parts,
        "markup_removed": markup_removed,
        "relationships_removed": rels_removed,
        "content_types_removed": content_types_removed,
        "zip_entries": len(zipfile.ZipFile(output_docx).namelist()),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Strip DOCX comments without rewriting unrelated package parts.")
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args(argv)
    try:
        payload = strip_comments(args.input, args.output)
    except Exception as exc:  # noqa: BLE001
        payload = {"status": "failed", "errors": [str(exc)]}
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["status"] == "stripped" else 1


if __name__ == "__main__":
    raise SystemExit(main())
