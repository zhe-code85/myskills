#! python3
"""Patch body paragraphs and tables in DOCX XML while preserving package parts."""

from __future__ import annotations

import argparse
import copy
import json
import zipfile
from pathlib import Path
from typing import Any

from lxml import etree as ET


W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
XML_NS = "http://www.w3.org/XML/1998/namespace"
NS = {"w": W_NS}


def w_tag(name: str) -> str:
    return f"{{{W_NS}}}{name}"


def load_operations(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("operations JSON must be a mapping")
    return data


def body_children(root: ET.Element, tag_name: str) -> list[ET.Element]:
    body = root.find("w:body", NS)
    if body is None:
        raise ValueError("word/document.xml has no w:body")
    return [child for child in list(body) if child.tag == w_tag(tag_name)]


def clear_paragraph(paragraph: ET.Element) -> None:
    ppr = paragraph.find("w:pPr", NS)
    for child in list(paragraph):
        if child is ppr:
            continue
        paragraph.remove(child)


def set_paragraph_text(paragraph: ET.Element, text: str) -> None:
    clear_paragraph(paragraph)
    if text == "":
        return
    run = ET.SubElement(paragraph, w_tag("r"))
    node = ET.SubElement(run, w_tag("t"))
    if text[:1].isspace() or text[-1:].isspace():
        node.set(f"{{{XML_NS}}}space", "preserve")
    node.text = text


def set_cell_text(cell: ET.Element, text: str, width: int) -> None:
    tcpr = ET.SubElement(cell, w_tag("tcPr"))
    tcw = ET.SubElement(tcpr, w_tag("tcW"))
    tcw.set(w_tag("w"), str(width))
    tcw.set(w_tag("type"), "dxa")
    paragraph = ET.SubElement(cell, w_tag("p"))
    set_paragraph_text(paragraph, text)


def set_table(table: ET.Element, rows_data: list[list[Any]]) -> None:
    if not rows_data:
        rows_data = [[""]]
    max_cols = max(max(len(row), 1) for row in rows_data)
    col_width = max(720, int(8640 / max_cols))
    tblpr = table.find("w:tblPr", NS)
    tblpr_copy = copy.deepcopy(tblpr) if tblpr is not None else None
    for child in list(table):
        table.remove(child)
    if tblpr_copy is not None:
        table.append(tblpr_copy)
    tbl_grid = ET.SubElement(table, w_tag("tblGrid"))
    for _ in range(max_cols):
        grid_col = ET.SubElement(tbl_grid, w_tag("gridCol"))
        grid_col.set(w_tag("w"), str(col_width))
    for values in rows_data:
        tr = ET.SubElement(table, w_tag("tr"))
        text_values = ["" if value is None else str(value) for value in values]
        text_values.extend([""] * (max_cols - len(text_values)))
        for value in text_values:
            tc = ET.SubElement(tr, w_tag("tc"))
            set_cell_text(tc, value, col_width)


def patch_document_xml(raw: bytes, operations: dict[str, Any]) -> tuple[bytes, dict[str, Any]]:
    parser = ET.XMLParser(resolve_entities=False, remove_blank_text=False)
    root = ET.fromstring(raw, parser)
    report: dict[str, Any] = {"paragraphs": [], "tables": []}

    paragraphs = body_children(root, "p")
    for item in operations.get("paragraphs", []):
        if not isinstance(item, dict):
            raise ValueError("paragraph operation must be a mapping")
        index = int(item["index"])
        if index < 0 or index >= len(paragraphs):
            raise IndexError(f"paragraph index out of range: {index}")
        set_paragraph_text(paragraphs[index], str(item.get("text", "")))
        report["paragraphs"].append(index)

    tables = body_children(root, "tbl")
    for item in operations.get("tables", []):
        if not isinstance(item, dict):
            raise ValueError("table operation must be a mapping")
        index = int(item["index"])
        if index < 0 or index >= len(tables):
            raise IndexError(f"table index out of range: {index}")
        rows = item.get("rows")
        if not isinstance(rows, list) or not all(isinstance(row, list) for row in rows):
            raise ValueError(f"table operation {index} must include rows as a list of lists")
        set_table(tables[index], rows)
        report["tables"].append(index)

    return ET.tostring(root, encoding="UTF-8", xml_declaration=True), report


def patch_docx(template: Path, operations: dict[str, Any], output: Path) -> dict[str, Any]:
    output.parent.mkdir(parents=True, exist_ok=True)
    patch_report: dict[str, Any] = {}
    with zipfile.ZipFile(template, "r") as src, zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as dst:
        for info in src.infolist():
            raw = src.read(info.filename)
            if info.filename == "word/document.xml":
                raw, patch_report = patch_document_xml(raw, operations)
            dst.writestr(info, raw)
    return {
        "status": "patched",
        "template": str(template),
        "output": str(output),
        "zip_entries": len(zipfile.ZipFile(output).namelist()),
        "operations": patch_report,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Patch DOCX body paragraphs/tables without dropping package resources.")
    parser.add_argument("--template", type=Path, required=True, help="Input DOCX")
    parser.add_argument("--operations", type=Path, required=True, help="JSON operations file")
    parser.add_argument("--output", type=Path, required=True, help="Output DOCX")
    parser.add_argument("--report", type=Path, help="Optional JSON report path")
    args = parser.parse_args(argv)

    try:
        payload = patch_docx(args.template, load_operations(args.operations), args.output)
    except Exception as exc:  # noqa: BLE001 - CLI should report compact failures.
        payload = {"status": "failed", "errors": [str(exc)]}

    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["status"] == "patched" else 1


if __name__ == "__main__":
    raise SystemExit(main())
