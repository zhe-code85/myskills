#! python3
"""Patch short text in a DOCX package while preserving unrelated ZIP parts."""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from lxml import etree


TEXT_PART_RE = re.compile(
    r"^(word/(document|header\d+|footer\d+|footnotes|endnotes|comments)\.xml|word/charts/.+\.xml|docProps/(core|app)\.xml)$"
)
XML_NS = "http://www.w3.org/XML/1998/namespace"
TEXT_NAMES = {
    "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t",
    "{http://schemas.openxmlformats.org/drawingml/2006/main}t",
}
TEXT_CONTAINER_NAMES = {
    "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p",
    "{http://schemas.openxmlformats.org/drawingml/2006/main}p",
}
VISUAL_NAMES = {
    "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}drawing",
    "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}pict",
    "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}object",
}
W_RUN = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}r"


@dataclass
class Replacement:
    old: str
    new: str
    count: int = 0


def load_replacements(path: Path | None, inline: list[str]) -> list[Replacement]:
    replacements: list[Replacement] = []
    if path:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            source = [{"old": old, "new": new} for old, new in data.items()]
        elif isinstance(data, list):
            source = data
        else:
            raise ValueError("replacement JSON must be a mapping or a list")
        for item in source:
            if not isinstance(item, dict) or "old" not in item or "new" not in item:
                raise ValueError("each replacement item must include old and new")
            replacements.append(Replacement(str(item["old"]), str(item["new"])))

    for item in inline:
        if "=" not in item:
            raise ValueError(f"inline replacement must use OLD=NEW form: {item}")
        old, new = item.split("=", 1)
        replacements.append(Replacement(old, new))

    if not replacements:
        raise ValueError("at least one replacement is required")
    return replacements


def patch_xml(
    raw: bytes,
    replacements: list[Replacement],
    part_name: str,
    remove_visuals: bool = False,
) -> tuple[bytes, dict[str, int], int]:
    text = raw.decode("utf-8")
    counts: dict[str, int] = {replacement.old: 0 for replacement in replacements}
    changed = False
    for replacement in replacements:
        variants = [
            (replacement.old, replacement.new),
            (html.escape(replacement.old, quote=False), html.escape(replacement.new, quote=False)),
        ]
        seen: set[str] = set()
        for old, new in variants:
            if old in seen:
                continue
            seen.add(old)
            occurrences = text.count(old)
            if occurrences:
                text = text.replace(old, new)
                changed = True
                replacement.count += occurrences
                counts[replacement.old] += occurrences

    xml_raw = text.encode("utf-8")
    try:
        root = etree.fromstring(xml_raw)
    except etree.XMLSyntaxError:
        return xml_raw, counts

    split_counts = patch_split_text_nodes(root, replacements)
    if any(split_counts.values()):
        changed = True
        for old, count in split_counts.items():
            counts[old] += count
    removed_visuals = remove_visual_runs(root) if remove_visuals else 0
    if removed_visuals:
        changed = True
    if not changed:
        return raw, counts, 0
    return etree.tostring(root, encoding="UTF-8", xml_declaration=text.lstrip().startswith("<?xml")), counts, removed_visuals


def patch_split_text_nodes(root: etree._Element, replacements: list[Replacement]) -> dict[str, int]:
    counts: dict[str, int] = {replacement.old: 0 for replacement in replacements}
    for container in root.iter():
        if container.tag not in TEXT_CONTAINER_NAMES:
            continue
        nodes = [node for node in container.iter() if node.tag in TEXT_NAMES]
        if not nodes:
            continue
        for replacement in replacements:
            while replace_once_in_text_nodes(nodes, replacement):
                replacement.count += 1
                counts[replacement.old] += 1
    return counts


def remove_visual_runs(root: etree._Element) -> int:
    removed = 0
    for visual in list(root.iter()):
        if visual.tag not in VISUAL_NAMES:
            continue
        node = visual
        while node.getparent() is not None and node.tag != W_RUN:
            node = node.getparent()
        parent = node.getparent()
        if parent is not None:
            parent.remove(node)
            removed += 1
    return removed


def replace_once_in_text_nodes(nodes: list[etree._Element], replacement: Replacement) -> bool:
    if not replacement.old or replacement.old == replacement.new:
        return False
    texts = [node.text or "" for node in nodes]
    combined = "".join(texts)
    start = combined.find(replacement.old)
    if start < 0:
        return False
    end = start + len(replacement.old)

    positions: list[tuple[int, int]] = []
    cursor = 0
    for text in texts:
        next_cursor = cursor + len(text)
        positions.append((cursor, next_cursor))
        cursor = next_cursor

    start_index = next(index for index, (_, node_end) in enumerate(positions) if start < node_end)
    end_index = next(index for index, (node_start, node_end) in enumerate(positions) if node_start < end <= node_end)

    start_node_start, _ = positions[start_index]
    end_node_start, _ = positions[end_index]
    start_text = texts[start_index]
    end_text = texts[end_index]
    prefix = start_text[: start - start_node_start]
    suffix = end_text[end - end_node_start :]

    nodes[start_index].text = prefix + replacement.new + suffix
    if nodes[start_index].text[:1].isspace() or nodes[start_index].text[-1:].isspace():
        nodes[start_index].set(f"{{{XML_NS}}}space", "preserve")
    for index in range(start_index + 1, end_index + 1):
        nodes[index].text = ""
    return True


def patch_docx(template: Path, output: Path, replacements: list[Replacement], remove_visual_parts: set[str] | None = None) -> dict[str, Any]:
    output.parent.mkdir(parents=True, exist_ok=True)
    part_counts: dict[str, dict[str, int]] = {}
    visual_counts: dict[str, int] = {}
    remove_visual_parts = remove_visual_parts or set()
    with zipfile.ZipFile(template, "r") as src, zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as dst:
        for info in src.infolist():
            raw = src.read(info.filename)
            if TEXT_PART_RE.match(info.filename):
                try:
                    raw, counts, removed_visuals = patch_xml(raw, replacements, info.filename, info.filename in remove_visual_parts)
                    if any(counts.values()):
                        part_counts[info.filename] = counts
                    if removed_visuals:
                        visual_counts[info.filename] = removed_visuals
                except UnicodeDecodeError:
                    pass
            dst.writestr(info, raw)

    return {
        "status": "patched",
        "template": str(template),
        "output": str(output),
        "zip_entries": len(zipfile.ZipFile(output).namelist()),
        "parts_changed": part_counts,
        "visuals_removed": visual_counts,
        "replacements": [{"old": item.old, "new": item.new, "count": item.count} for item in replacements],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Patch short DOCX text without dropping media/chart/embedding parts.")
    parser.add_argument("--template", type=Path, required=True, help="Input DOCX")
    parser.add_argument("--output", type=Path, required=True, help="Output DOCX")
    parser.add_argument("--replacements-json", type=Path, help="JSON mapping or list of {old,new} replacements")
    parser.add_argument("--replace", action="append", default=[], help="Inline OLD=NEW replacement; may repeat")
    parser.add_argument("--remove-visual-part", action="append", default=[], help="Remove drawing/pict/object runs from the named Word XML part; may repeat")
    parser.add_argument("--strict", action="store_true", help="Fail if any replacement is not found")
    parser.add_argument("--report", type=Path, help="Optional JSON report path")
    args = parser.parse_args(argv)

    try:
        replacements = load_replacements(args.replacements_json, args.replace)
        payload = patch_docx(args.template, args.output, replacements, set(args.remove_visual_part))
        missing = [item.old for item in replacements if item.count == 0]
        if args.strict and missing:
            payload["status"] = "failed"
            payload["errors"] = [f"replacement text not found: {old}" for old in missing]
    except Exception as exc:  # noqa: BLE001 - CLI should report a compact failure.
        payload = {"status": "failed", "errors": [str(exc)]}

    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["status"] == "patched" else 1


if __name__ == "__main__":
    raise SystemExit(main())
