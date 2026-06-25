#! python3
"""Run bounded Word Find/Replace across body, headers, footers, and textboxes."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any


WD_REPLACE_ALL = 2
WD_FIND_CONTINUE = 1
HEADER_FOOTER_TYPES = (1, 2, 3)


def load_replacements(path: Path | None, inline: list[str]) -> list[tuple[str, str]]:
    replacements: list[tuple[str, str]] = []
    if path:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            replacements.extend((str(k), str(v)) for k, v in data.items())
        elif isinstance(data, list):
            for item in data:
                replacements.append((str(item["old"]), str(item["new"])))
        else:
            raise ValueError("replacement JSON must be a mapping or list")
    for item in inline:
        if "=" not in item:
            raise ValueError(f"replacement must use OLD=NEW: {item}")
        old, new = item.split("=", 1)
        replacements.append((old, new))
    if not replacements:
        raise ValueError("at least one replacement is required")
    return replacements


def replace_in_range(rng: Any, old: str, new: str) -> None:
    find = rng.Find
    find.ClearFormatting()
    find.Replacement.ClearFormatting()
    find.Text = old
    find.Replacement.Text = new
    find.Forward = True
    find.Wrap = WD_FIND_CONTINUE
    find.Format = False
    find.MatchCase = False
    find.MatchWholeWord = False
    find.MatchWildcards = False
    find.Execute(Replace=WD_REPLACE_ALL)


def replace_in_shape(shape: Any, old: str, new: str) -> bool:
    try:
        if not shape.TextFrame.HasText:
            return False
        replace_in_range(shape.TextFrame.TextRange, old, new)
        return True
    except Exception:  # noqa: BLE001 - shapes vary by Word version and type.
        return False


def iter_collection(collection: Any) -> list[Any]:
    items: list[Any] = []
    try:
        count = int(collection.Count)
    except Exception:  # noqa: BLE001
        return items
    for index in range(1, count + 1):
        try:
            items.append(collection(index))
        except Exception:  # noqa: BLE001
            continue
    return items


def replace_in_doc_scope(doc: Any, old: str, new: str) -> dict[str, int]:
    counts = {"ranges": 0, "shapes": 0}

    replace_in_range(doc.Content, old, new)
    counts["ranges"] += 1

    for shape in iter_collection(doc.Shapes):
        if replace_in_shape(shape, old, new):
            counts["shapes"] += 1

    for section in iter_collection(doc.Sections):
        for header_footer_type in HEADER_FOOTER_TYPES:
            for part_name in ("Headers", "Footers"):
                try:
                    part = getattr(section, part_name)(header_footer_type)
                    replace_in_range(part.Range, old, new)
                    counts["ranges"] += 1
                    for shape in iter_collection(part.Shapes):
                        if replace_in_shape(shape, old, new):
                            counts["shapes"] += 1
                except Exception:  # noqa: BLE001 - first/even page parts may not exist or be linked.
                    continue

    return counts


def run(input_docx: Path, output_docx: Path, replacements: list[tuple[str, str]]) -> dict[str, Any]:
    import pythoncom
    import win32com.client

    output_docx.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(input_docx, output_docx)

    pythoncom.CoInitialize()
    word = win32com.client.DispatchEx("Word.Application")
    word.Visible = False
    word.DisplayAlerts = 0
    payload: dict[str, Any] = {"status": "started", "input": str(input_docx), "output": str(output_docx), "replacements": []}
    try:
        doc = word.Documents.Open(
            str(output_docx.resolve()),
            ConfirmConversions=False,
            ReadOnly=False,
            AddToRecentFiles=False,
            OpenAndRepair=True,
            NoEncodingDialog=True,
        )
        try:
            for old, new in replacements:
                counts = replace_in_doc_scope(doc, old, new)
                payload["replacements"].append({"old": old, "new": new, **counts})
            doc.Save()
            payload["status"] = "replaced"
        finally:
            doc.Close(False)
    except Exception as exc:  # noqa: BLE001
        payload["status"] = "failed"
        payload["error"] = str(exc)
    finally:
        word.Quit()
        pythoncom.CoUninitialize()
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Word find/replace for final DOCX cleanup.")
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--replacements-json", type=Path)
    parser.add_argument("--replace", action="append", default=[])
    parser.add_argument("--report", type=Path)
    args = parser.parse_args(argv)
    try:
        payload = run(args.input, args.output, load_replacements(args.replacements_json, args.replace))
    except Exception as exc:  # noqa: BLE001
        payload = {"status": "failed", "errors": [str(exc)]}
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["status"] == "replaced" else 1


if __name__ == "__main__":
    raise SystemExit(main())
