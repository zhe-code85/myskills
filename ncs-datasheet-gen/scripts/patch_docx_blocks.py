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
PRESERVE_PARAGRAPH_MARKUP = {
    "bookmarkStart",
    "bookmarkEnd",
    "commentRangeStart",
    "commentRangeEnd",
    "permStart",
    "permEnd",
}
PRESERVE_PARAGRAPH_VISUALS = {
    "drawing",
    "pict",
    "object",
}


def w_tag(name: str) -> str:
    return f"{{{W_NS}}}{name}"


def local_name(element: ET.Element) -> str:
    return ET.QName(element).localname


def contains_visual(element: ET.Element) -> bool:
    return (
        element.find(".//w:drawing", NS) is not None
        or element.find(".//w:pict", NS) is not None
        or element.find(".//w:object", NS) is not None
    )


def contains_text(element: ET.Element) -> bool:
    return any((text.text or "").strip() for text in element.findall(".//w:t", NS))


def load_operations(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("operations JSON must be a mapping")
    return data


def require_source_slot(item: dict[str, Any], kind: str) -> None:
    if not item.get("source_slot"):
        raise ValueError(f"{kind} operation must include source_slot when --require-source-slots is used")


def body_children(root: ET.Element, tag_name: str) -> list[ET.Element]:
    body = root.find("w:body", NS)
    if body is None:
        raise ValueError("word/document.xml has no w:body")
    return [child for child in list(body) if child.tag == w_tag(tag_name)]


def clear_paragraph(paragraph: ET.Element, *, preserve_visuals: bool = False) -> None:
    ppr = paragraph.find("w:pPr", NS)
    for child in list(paragraph):
        if child is ppr:
            continue
        if local_name(child) in PRESERVE_PARAGRAPH_MARKUP:
            continue
        if preserve_visuals and (local_name(child) in PRESERVE_PARAGRAPH_VISUALS or contains_visual(child)):
            continue
        paragraph.remove(child)


def neutralize_empty_paragraph(paragraph: ET.Element) -> None:
    ppr = paragraph.find("w:pPr", NS)
    if ppr is None:
        return
    for child in list(ppr):
        if local_name(child) in {"pStyle", "numPr", "ind", "tabs"}:
            ppr.remove(child)


def paragraph_text_insert_index(paragraph: ET.Element) -> int:
    children = list(paragraph)
    for index, child in enumerate(children):
        if local_name(child) == "bookmarkEnd":
            return index
    return len(children)


def set_paragraph_text(paragraph: ET.Element, text: str, preserve_visuals: bool | None = None) -> None:
    if preserve_visuals is None:
        preserve_visuals = text == "" or contains_visual(paragraph)
    old_rpr = None
    old_run = paragraph.find("w:r", NS)
    if old_run is not None:
        old_rpr = old_run.find("w:rPr", NS)
        old_rpr = copy.deepcopy(old_rpr) if old_rpr is not None else None
    clear_paragraph(paragraph, preserve_visuals=preserve_visuals)
    if text == "":
        neutralize_empty_paragraph(paragraph)
        return
    run = ET.Element(w_tag("r"))
    if old_rpr is not None:
        run.append(old_rpr)
    node = ET.SubElement(run, w_tag("t"))
    if text[:1].isspace() or text[-1:].isspace():
        node.set(f"{{{XML_NS}}}space", "preserve")
    node.text = text
    paragraph.insert(paragraph_text_insert_index(paragraph), run)


def remove_paragraph_visuals(paragraph: ET.Element) -> int:
    removed = 0
    for child in list(paragraph):
        if local_name(child) in PRESERVE_PARAGRAPH_VISUALS or contains_visual(child):
            paragraph.remove(child)
            removed += 1
    return removed


def paragraph_has_section_properties(paragraph: ET.Element) -> bool:
    return paragraph.find(".//w:sectPr", NS) is not None


def paragraph_is_empty(paragraph: ET.Element) -> bool:
    return not contains_text(paragraph) and not contains_visual(paragraph)


def set_cell_text(cell: ET.Element, text: str, width: int, tcpr_template: ET.Element | None = None) -> None:
    if tcpr_template is not None:
        cell.append(copy.deepcopy(tcpr_template))
    else:
        tcpr = ET.SubElement(cell, w_tag("tcPr"))
        tcw = ET.SubElement(tcpr, w_tag("tcW"))
        tcw.set(w_tag("w"), str(width))
        tcw.set(w_tag("type"), "dxa")
    paragraph = ET.SubElement(cell, w_tag("p"))
    set_paragraph_text(paragraph, text)


def default_table_properties() -> ET.Element:
    tblpr = ET.Element(w_tag("tblPr"))
    borders = ET.SubElement(tblpr, w_tag("tblBorders"))
    for side in ("top", "left", "bottom", "right", "insideH", "insideV"):
        border = ET.SubElement(borders, w_tag(side))
        border.set(w_tag("val"), "single")
        border.set(w_tag("sz"), "4")
        border.set(w_tag("space"), "0")
        border.set(w_tag("color"), "auto")
    return tblpr


def table_row_templates(table: ET.Element) -> list[dict[str, Any]]:
    templates: list[dict[str, Any]] = []
    rows = table.findall("w:tr", NS)
    selected_rows = rows[:1]
    body_row = rows[1] if len(rows) > 1 else None
    for candidate in rows[1:]:
        cells = candidate.findall("w:tc", NS)
        fills = []
        for cell in cells:
            shd = cell.find(".//w:shd", NS)
            fills.append(shd.get(w_tag("fill")) if shd is not None else "")
        if len(cells) >= 2 and not (fills and all(fill == "000000" for fill in fills)):
            body_row = candidate
            break
    if body_row is not None:
        selected_rows.append(body_row)
    for row in selected_rows:
        templates.append({
            "trPr": copy.deepcopy(row.find("w:trPr", NS)),
            "tcPr": [copy.deepcopy(cell.find("w:tcPr", NS)) for cell in row.findall("w:tc", NS)],
        })
    return templates


def set_table(table: ET.Element, rows_data: list[list[Any]]) -> None:
    if not rows_data:
        rows_data = [[""]]
    max_cols = max(max(len(row), 1) for row in rows_data)
    col_width = max(720, int(8640 / max_cols))
    row_templates = table_row_templates(table)
    tblpr = table.find("w:tblPr", NS)
    tblpr_copy = copy.deepcopy(tblpr) if tblpr is not None else None
    for child in list(table):
        table.remove(child)
    table.append(tblpr_copy if tblpr_copy is not None else default_table_properties())
    tbl_grid = ET.SubElement(table, w_tag("tblGrid"))
    for _ in range(max_cols):
        grid_col = ET.SubElement(tbl_grid, w_tag("gridCol"))
        grid_col.set(w_tag("w"), str(col_width))
    for row_index, values in enumerate(rows_data):
        tr = ET.SubElement(table, w_tag("tr"))
        row_template = row_templates[0] if row_index == 0 and row_templates else (row_templates[1] if len(row_templates) > 1 else None)
        if row_template and row_template.get("trPr") is not None:
            tr.append(copy.deepcopy(row_template["trPr"]))
        text_values = ["" if value is None else str(value) for value in values]
        text_values.extend([""] * (max_cols - len(text_values)))
        for col_index, value in enumerate(text_values):
            tc = ET.SubElement(tr, w_tag("tc"))
            tc_templates = row_template.get("tcPr", []) if row_template else []
            tcpr = tc_templates[col_index] if col_index < len(tc_templates) else None
            set_cell_text(tc, value, col_width, tcpr)


def insert_table_after_paragraph(root: ET.Element, paragraph: ET.Element, rows_data: list[list[Any]]) -> None:
    body = root.find("w:body", NS)
    if body is None:
        raise ValueError("word/document.xml has no w:body")
    table = ET.Element(w_tag("tbl"))
    set_table(table, rows_data)
    body.insert(list(body).index(paragraph) + 1, table)


def normalize_range(item: dict[str, Any], paragraph_count: int, kind: str) -> tuple[int, int]:
    start = int(item["start"])
    end = int(item["end"])
    if start < 0 or end < 0 or start > end or end >= paragraph_count:
        raise IndexError(f"{kind} paragraph range out of bounds: {start}..{end}")
    return start, end


def remove_empty_trailing_paragraphs(root: ET.Element) -> int:
    body = root.find("w:body", NS)
    if body is None:
        raise ValueError("word/document.xml has no w:body")
    removed = 0
    children = list(body)
    index = len(children) - 1
    while index >= 0 and children[index].tag == w_tag("sectPr"):
        index -= 1
    while index >= 0:
        child = children[index]
        if child.tag != w_tag("p"):
            break
        if paragraph_has_section_properties(child) or not paragraph_is_empty(child):
            break
        body.remove(child)
        removed += 1
        index -= 1
    return removed


def patch_document_xml(raw: bytes, operations: dict[str, Any], *, require_source_slots: bool = False) -> tuple[bytes, dict[str, Any]]:
    parser = ET.XMLParser(resolve_entities=False, remove_blank_text=False)
    root = ET.fromstring(raw, parser)
    report: dict[str, Any] = {
        "paragraphs": [],
        "clear_paragraph_ranges": [],
        "replace_paragraph_ranges": [],
        "remove_visuals_in_ranges": [],
        "tables": [],
        "remove_tables": [],
        "insert_tables_after_paragraphs": [],
        "remove_empty_trailing_paragraphs": 0,
    }

    paragraphs = body_children(root, "p")
    for item in operations.get("clear_paragraph_ranges", []):
        if not isinstance(item, dict):
            raise ValueError("clear paragraph range operation must be a mapping")
        if require_source_slots:
            require_source_slot(item, "clear paragraph range")
        start, end = normalize_range(item, len(paragraphs), "clear_paragraph_ranges")
        preserve_visuals = item.get("preserve_visuals", True)
        if not isinstance(preserve_visuals, bool):
            raise ValueError(f"clear paragraph range {start}..{end} preserve_visuals must be a boolean")
        for index in range(start, end + 1):
            set_paragraph_text(paragraphs[index], "", preserve_visuals=preserve_visuals)
        report["clear_paragraph_ranges"].append({"start": start, "end": end})

    paragraphs = body_children(root, "p")
    for item in operations.get("replace_paragraph_ranges", []):
        if not isinstance(item, dict):
            raise ValueError("replace paragraph range operation must be a mapping")
        if require_source_slots:
            require_source_slot(item, "replace paragraph range")
        start, end = normalize_range(item, len(paragraphs), "replace_paragraph_ranges")
        replacement = item.get("paragraphs")
        if not isinstance(replacement, list):
            raise ValueError(f"replace paragraph range {start}..{end} must include paragraphs list")
        if len(replacement) > (end - start + 1):
            raise ValueError(f"replace paragraph range {start}..{end} has too many replacement paragraphs")
        preserve_visuals = item.get("preserve_visuals")
        if preserve_visuals is not None and not isinstance(preserve_visuals, bool):
            raise ValueError(f"replace paragraph range {start}..{end} preserve_visuals must be a boolean")
        for offset, text in enumerate(replacement):
            set_paragraph_text(paragraphs[start + offset], str(text), preserve_visuals=preserve_visuals)
        for index in range(start + len(replacement), end + 1):
            set_paragraph_text(paragraphs[index], "", preserve_visuals=False)
        report["replace_paragraph_ranges"].append({"start": start, "end": end, "written": len(replacement)})

    paragraphs = body_children(root, "p")
    for item in operations.get("remove_visuals_in_ranges", []):
        if not isinstance(item, dict):
            raise ValueError("remove visuals in range operation must be a mapping")
        if require_source_slots:
            require_source_slot(item, "remove visuals in range")
        start, end = normalize_range(item, len(paragraphs), "remove_visuals_in_ranges")
        removed = 0
        for index in range(start, end + 1):
            removed += remove_paragraph_visuals(paragraphs[index])
        report["remove_visuals_in_ranges"].append({"start": start, "end": end, "removed": removed})

    if operations.get("remove_empty_trailing_paragraphs"):
        item = operations["remove_empty_trailing_paragraphs"]
        if isinstance(item, dict):
            if require_source_slots:
                require_source_slot(item, "remove empty trailing paragraphs")
        elif require_source_slots:
            raise ValueError("remove_empty_trailing_paragraphs must include source_slot when --require-source-slots is used")
        report["remove_empty_trailing_paragraphs"] = remove_empty_trailing_paragraphs(root)

    paragraphs = body_children(root, "p")
    for item in operations.get("paragraphs", []):
        if not isinstance(item, dict):
            raise ValueError("paragraph operation must be a mapping")
        if require_source_slots:
            require_source_slot(item, "paragraph")
        index = int(item["index"])
        if index < 0 or index >= len(paragraphs):
            raise IndexError(f"paragraph index out of range: {index}")
        preserve_visuals = item.get("preserve_visuals")
        if preserve_visuals is not None and not isinstance(preserve_visuals, bool):
            raise ValueError(f"paragraph operation {index} preserve_visuals must be a boolean")
        set_paragraph_text(paragraphs[index], str(item.get("text", "")), preserve_visuals=preserve_visuals)
        report["paragraphs"].append(index)

    tables = body_children(root, "tbl")
    for item in operations.get("tables", []):
        if not isinstance(item, dict):
            raise ValueError("table operation must be a mapping")
        if require_source_slots:
            require_source_slot(item, "table")
        index = int(item["index"])
        if index < 0 or index >= len(tables):
            raise IndexError(f"table index out of range: {index}")
        rows = item.get("rows")
        if not isinstance(rows, list) or not all(isinstance(row, list) for row in rows):
            raise ValueError(f"table operation {index} must include rows as a list of lists")
        set_table(tables[index], rows)
        report["tables"].append(index)

    tables = body_children(root, "tbl")
    remove_indexes = sorted({int(index) for index in operations.get("remove_tables", [])}, reverse=True)
    for index in remove_indexes:
        if index < 0 or index >= len(tables):
            raise IndexError(f"table index out of range for removal: {index}")
        parent = tables[index].getparent()
        if parent is None:
            raise ValueError(f"table {index} has no parent")
        parent.remove(tables[index])
        report["remove_tables"].append(index)

    paragraphs = body_children(root, "p")
    for item in operations.get("insert_tables_after_paragraphs", []):
        if not isinstance(item, dict):
            raise ValueError("insert table operation must be a mapping")
        if require_source_slots:
            require_source_slot(item, "insert table")
        index = int(item["index"])
        if index < 0 or index >= len(paragraphs):
            raise IndexError(f"paragraph index out of range for inserted table: {index}")
        rows = item.get("rows")
        if not isinstance(rows, list) or not all(isinstance(row, list) for row in rows):
            raise ValueError(f"insert table operation {index} must include rows as a list of lists")
        insert_table_after_paragraph(root, paragraphs[index], rows)
        report["insert_tables_after_paragraphs"].append(index)

    return ET.tostring(root, encoding="UTF-8", xml_declaration=True), report


def patch_docx(template: Path, operations: dict[str, Any], output: Path, *, require_source_slots: bool = False) -> dict[str, Any]:
    output.parent.mkdir(parents=True, exist_ok=True)
    patch_report: dict[str, Any] = {}
    with zipfile.ZipFile(template, "r") as src, zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as dst:
        for info in src.infolist():
            raw = src.read(info.filename)
            if info.filename == "word/document.xml":
                raw, patch_report = patch_document_xml(raw, operations, require_source_slots=require_source_slots)
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
    parser.add_argument("--require-source-slots", action="store_true", help="Require source_slot on mutating operations")
    args = parser.parse_args(argv)

    try:
        payload = patch_docx(args.template, load_operations(args.operations), args.output, require_source_slots=args.require_source_slots)
    except Exception as exc:  # noqa: BLE001 - CLI should report compact failures.
        payload = {"status": "failed", "errors": [str(exc)]}

    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["status"] == "patched" else 1


if __name__ == "__main__":
    raise SystemExit(main())
