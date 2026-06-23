"""Verify generated datasheet DOCX structure, required text, and risk markings."""

from __future__ import annotations

import argparse
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET


NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
RED_VALUES = {"C00000", "FF0000", "E60000", "D00000"}


def read_xml(package: zipfile.ZipFile, name: str) -> ET.Element | None:
    if name not in package.namelist():
        return None
    try:
        return ET.fromstring(package.read(name))
    except ET.ParseError:
        return None


def attr(node: ET.Element | None, name: str) -> str | None:
    if node is None:
        return None
    return node.attrib.get(W + name)


def text_of(node: ET.Element) -> str:
    return "".join(text.text or "" for text in node.findall(".//w:t", NS))


def local_name(node: ET.Element) -> str:
    return node.tag.rsplit("}", 1)[-1]


def body_text_of(document: ET.Element) -> str:
    body = document.find(".//w:body", NS)
    if body is None:
        return ""
    texts = []
    for child in list(body):
        if local_name(child) in {"p", "tbl"}:
            text = text_of(child)
            if text:
                texts.append(text)
    return "\n".join(texts)


def body_section_properties(document: ET.Element) -> ET.Element | None:
    body = document.find(".//w:body", NS)
    if body is None:
        return None
    for child in list(body):
        if local_name(child) == "sectPr":
            return child
    return None


def section_header_footer_ref_count(section: ET.Element | None) -> int:
    if section is None:
        return 0
    return len(section.findall("./w:headerReference", NS)) + len(section.findall("./w:footerReference", NS))


def section_is_two_column(section: ET.Element | None) -> bool:
    if section is None:
        return False
    cols = section.find("./w:cols", NS)
    return attr(cols, "num") == "2"


def collect_named_parts(package: zipfile.ZipFile) -> list[tuple[str, ET.Element]]:
    parts = ["word/document.xml"]
    parts.extend(name for name in package.namelist() if name.startswith("word/header") or name.startswith("word/footer"))
    roots: list[tuple[str, ET.Element]] = []
    for part in parts:
        root = read_xml(package, part)
        if root is not None:
            roots.append((part, root))
    return roots


def collect_parts(package: zipfile.ZipFile) -> list[ET.Element]:
    return [root for _, root in collect_named_parts(package)]


def style_ids(styles_root: ET.Element | None) -> set[str]:
    if styles_root is None:
        return set()
    ids = set()
    for style in styles_root.findall(".//w:style", NS):
        value = attr(style, "styleId")
        if value:
            ids.add(value)
    return ids


def is_comment_part(name: str) -> bool:
    return name.startswith("word/comments") or name == "word/people.xml"


def comment_reference_counts(roots: list[ET.Element]) -> dict[str, int]:
    tags = ("commentRangeStart", "commentRangeEnd", "commentReference", "annotationRef")
    return {tag: sum(len(root.findall(f".//w:{tag}", NS)) for root in roots) for tag in tags}


def risk_run_counts(document: ET.Element, marker: str) -> tuple[int, int]:
    total = 0
    red = 0
    for run in document.findall(".//w:r", NS):
        run_text = text_of(run)
        if marker not in run_text:
            continue
        total += 1
        color = run.find("./w:rPr/w:color", NS)
        value = attr(color, "val")
        if value and value.upper() in RED_VALUES:
            red += 1
    return total, red


def verify(args: argparse.Namespace) -> list[str]:
    failures: list[str] = []
    if not args.docx.exists():
        return [f"missing DOCX: {args.docx}"]
    with zipfile.ZipFile(args.docx) as package:
        document = read_xml(package, "word/document.xml")
        styles = read_xml(package, "word/styles.xml")
        if document is None:
            return ["missing or unreadable word/document.xml"]
        named_roots = collect_named_parts(package)
        roots = [root for _, root in named_roots]
        all_text = "\n".join(text_of(root) for root in roots)
        header_footer_text = "\n".join(
            text_of(root)
            for name, root in named_roots
            if name.startswith("word/header") or name.startswith("word/footer")
        )

        for expected in args.expect or []:
            if expected not in all_text:
                failures.append(f"missing required text: {expected}")

        for forbidden in args.forbid_text or []:
            if forbidden in all_text:
                failures.append(f"forbidden text found: {forbidden}")

        for forbidden in args.forbid_header_footer_text or []:
            if forbidden in header_footer_text:
                failures.append(f"forbidden header/footer text found: {forbidden}")

        ids = style_ids(styles)
        for required in args.require_style or []:
            if required not in ids:
                failures.append(f"missing required styleId: {required}")

        table_count = len(document.findall(".//w:tbl", NS))
        drawing_count = len(document.findall(".//w:drawing", NS))
        if table_count < args.min_tables:
            failures.append(f"expected at least {args.min_tables} tables, found {table_count}")
        if drawing_count < args.min_drawings:
            failures.append(f"expected at least {args.min_drawings} drawings, found {drawing_count}")

        if args.require_two_column and not document.findall(".//w:cols[@w:num='2']", NS):
            failures.append("missing two-column section")
        if args.require_column_break and not document.findall(".//w:br[@w:type='column']", NS):
            failures.append("missing column break")

        body_text = body_text_of(document)
        for forbidden in args.forbid_body_text or []:
            if forbidden in body_text:
                failures.append(f"forbidden body text found: {forbidden}")

        body_section = body_section_properties(document)
        if args.require_body_two_column and not section_is_two_column(body_section):
            failures.append("missing body-level two-column section")
        if section_header_footer_ref_count(body_section) < args.min_body_section_header_footer_refs:
            failures.append(
                "body-level header/footer references below minimum: "
                f"{section_header_footer_ref_count(body_section)}/{args.min_body_section_header_footer_refs}"
            )

        if args.forbid_comments:
            comment_parts = sorted(name for name in package.namelist() if is_comment_part(name))
            if comment_parts:
                failures.append(f"template comment parts remain: {', '.join(comment_parts)}")
            for tag, count in comment_reference_counts(roots).items():
                if count:
                    failures.append(f"template comment reference remains: {tag} ({count})")

        for marker in args.risk_marker or []:
            total, red = risk_run_counts(document, marker)
            if total == 0:
                failures.append(f"risk marker not found: {marker}")
            elif total != red:
                failures.append(f"risk marker not fully red: {marker} ({red}/{total})")

    return failures


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Verify generated datasheet DOCX content and formatting signals.")
    parser.add_argument("--docx", type=Path, required=True)
    parser.add_argument("--expect", action="append", help="Required text; repeatable")
    parser.add_argument("--risk-marker", action="append", help="Risk marker that must appear in red; repeatable")
    parser.add_argument("--require-style", action="append", help="Required styleId in styles.xml; repeatable")
    parser.add_argument("--min-tables", type=int, default=0)
    parser.add_argument("--min-drawings", type=int, default=0)
    parser.add_argument("--require-two-column", action="store_true")
    parser.add_argument("--require-column-break", action="store_true")
    parser.add_argument("--forbid-comments", action="store_true", help="Fail if inherited Word comments or comment references remain")
    parser.add_argument("--forbid-text", action="append", help="Text that must not appear in body, headers, or footers; repeatable")
    parser.add_argument("--forbid-header-footer-text", action="append", help="Text that must not appear in headers or footers; repeatable")
    parser.add_argument("--forbid-body-text", action="append", help="Text that must not appear in the generated document body; repeatable")
    parser.add_argument("--require-body-two-column", action="store_true", help="Require the body-level section properties to be two-column")
    parser.add_argument("--min-body-section-header-footer-refs", type=int, default=0, help="Minimum body-level header/footer references")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    failures = verify(args)
    if failures:
        print("FAIL:")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print(f"PASS: {args.docx}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
