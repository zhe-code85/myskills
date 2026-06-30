#! python3
"""Smoke-test DOCX template-copy replacement without invoking skill workflows."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any

from lxml import etree as ET


SCRIPT_DIR = Path(__file__).parent
W_T = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t"
A_T = "{http://schemas.openxmlformats.org/drawingml/2006/main}t"
TEXT_TAGS = {W_T, A_T}


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def run_command(command: list[str], log_dir: Path, name: str) -> dict[str, Any]:
    log_dir.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(command, check=False, capture_output=True, text=True, encoding="utf-8")
    (log_dir / f"{name}.command.txt").write_text(" ".join(command), encoding="utf-8")
    (log_dir / f"{name}.stdout.txt").write_text(result.stdout, encoding="utf-8")
    (log_dir / f"{name}.stderr.txt").write_text(result.stderr, encoding="utf-8")
    payload = {"name": name, "returncode": result.returncode, "command": command}
    try:
        payload["json"] = json.loads(result.stdout)
    except json.JSONDecodeError:
        payload["stdout"] = result.stdout
        payload["stderr"] = result.stderr
    return payload


def py_command(script: str, *args: str | Path) -> list[str]:
    return [sys.executable, str(SCRIPT_DIR / script), *[str(arg) for arg in args]]


def default_replacements(product: str, company: str, title: str) -> list[dict[str, str]]:
    return [
        {"old": "JWXXXX", "new": product},
        {"old": "JWxxxx", "new": product},
        {"old": "JW5212", "new": product},
        {"old": "JWXX", "new": company},
        {"old": "JWQ", "new": company},
        {"old": "JoulWatt", "new": company},
        {"old": "Joulwatt", "new": company},
        {"old": "JOULWATT", "new": company},
        {"old": "1A, 5V Synchronous Buck Converter", "new": title},
        {"old": "1A, 5V Synchronous Clock Buffer Converter", "new": title},
        {"old": "buck switching regulator", "new": "LVDS clock buffer"},
        {"old": "Buck Switching Regulator", "new": "LVDS Clock Buffer"},
        {"old": "buck converter", "new": "clock buffer"},
        {"old": "Buck Converter", "new": "Clock Buffer"},
        {"old": "switching regulator", "new": "clock buffer"},
        {"old": "Switching Regulator", "new": "Clock Buffer"},
        {"old": "Soft-start", "new": "Output enable"},
        {"old": "Soft-Start", "new": "Output Enable"},
        {"old": "Soft Start", "new": "Output Enable"},
        {"old": "soft start", "new": "output enable"},
        {"old": "soft-start", "new": "output enable"},
        {"old": "Current Limit", "new": "Output Control"},
        {"old": "current limit", "new": "output control"},
        {"old": "DFN4", "new": "VQFN"},
    ]


def visible_text_by_part(docx: Path) -> dict[str, str]:
    texts: dict[str, str] = {}
    with zipfile.ZipFile(docx) as package:
        for name in package.namelist():
            if not name.startswith("word/") or not name.endswith(".xml"):
                continue
            if "/media/" in name or "/embeddings/" in name:
                continue
            try:
                root = ET.fromstring(package.read(name))
            except ET.XMLSyntaxError:
                continue
            text = "\n".join(node.text or "" for node in root.iter() if node.tag in TEXT_TAGS)
            if text:
                texts[name] = text
    return texts


def find_residuals(docx: Path, old_terms: list[str]) -> dict[str, list[str]]:
    texts = visible_text_by_part(docx)
    residuals: dict[str, list[str]] = {}
    for part, text in texts.items():
        folded = text.lower()
        hits = sorted({term for term in old_terms if term and term.lower() in folded})
        if hits:
            residuals[part] = hits
    return residuals


def check_toc_bookmarks(docx: Path) -> dict[str, Any]:
    with zipfile.ZipFile(docx) as package:
        root = ET.fromstring(package.read("word/document.xml"))
    bookmark_names = {
        node.get("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}name")
        for node in root.findall(
            ".//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}bookmarkStart"
        )
    }
    refs: list[str] = []
    for node in root.findall(".//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}instrText"):
        text = node.text or ""
        refs.extend(match.group(1) for match in re.finditer(r"PAGEREF\s+([^\\\s]+)", text))
        refs.extend(match.group(1) for match in re.finditer(r'HYPERLINK\s+\\l\s+"?([^"\\\s]+)', text))
    missing = sorted({ref for ref in refs if ref and ref not in bookmark_names})
    return {
        "status": "passed" if not missing else "failed",
        "bookmark_count": len([name for name in bookmark_names if name]),
        "toc_refs": sorted(set(refs)),
        "missing": missing,
    }


def load_fidelity_report(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        return {"status": "failed", "errors": [str(exc)]}


def safe_body_indices(template: Path) -> tuple[list[int], int | None]:
    with zipfile.ZipFile(template) as package:
        root = ET.fromstring(package.read("word/document.xml"))
    w_ns = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
    body = root.find(f"{w_ns}body")
    if body is None:
        raise ValueError("template has no word/document.xml body")
    paragraph_indices: list[int] = []
    table_index: int | None = None
    p_count = 0
    tbl_count = 0
    for child in body:
        if child.tag == f"{w_ns}p":
            text = "".join(node.text or "" for node in child.iter(W_T)).strip()
            has_field = any(ET.QName(node).localname in {"fldChar", "instrText"} for node in child.iter())
            if text and not has_field:
                paragraph_indices.append(p_count)
            p_count += 1
        elif child.tag == f"{w_ns}tbl":
            if table_index is None:
                table_index = tbl_count
            tbl_count += 1
    return paragraph_indices, table_index


def body_direct_texts(template: Path) -> tuple[list[str], list[str]]:
    with zipfile.ZipFile(template) as package:
        root = ET.fromstring(package.read("word/document.xml"))
    w_ns = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
    body = root.find(f"{w_ns}body")
    if body is None:
        raise ValueError("template has no word/document.xml body")
    paragraphs: list[str] = []
    tables: list[str] = []
    for child in body:
        text = " ".join(node.text or "" for node in child.iter() if node.tag in TEXT_TAGS).strip()
        if child.tag == f"{w_ns}p":
            paragraphs.append(text)
        elif child.tag == f"{w_ns}tbl":
            tables.append(text)
    return paragraphs, tables


def check_block_length_budget(
    template: Path,
    block_ops: dict[str, Any],
    *,
    max_text_ratio: float,
    max_added_chars: int,
) -> dict[str, Any]:
    paragraphs, tables = body_direct_texts(template)
    errors: list[str] = []
    items: list[dict[str, Any]] = []

    def append_item(kind: str, index: int, old_text: str, new_text: str) -> None:
        old_len = len(old_text)
        new_len = len(new_text)
        added = new_len - old_len
        ratio = (new_len / old_len) if old_len else float("inf")
        item = {"kind": kind, "index": index, "old_len": old_len, "new_len": new_len, "added": added, "ratio": ratio}
        items.append(item)
        if added > max_added_chars and ratio > max_text_ratio:
            errors.append(
                f"{kind} {index} exceeds length budget: old={old_len}, new={new_len}, ratio={ratio:.2f}, added={added}"
            )

    for item in block_ops.get("paragraphs", []):
        index = int(item["index"])
        append_item("paragraph", index, paragraphs[index] if 0 <= index < len(paragraphs) else "", str(item.get("text", "")))

    for item in block_ops.get("tables", []):
        index = int(item["index"])
        new_text = " ".join(str(cell) for row in item.get("rows", []) for cell in row)
        append_item("table", index, tables[index] if 0 <= index < len(tables) else "", new_text)

    return {"status": "passed" if not errors else "failed", "items": items, "errors": errors}


def make_block_ops(template: Path, product: str, stress_long_text: bool) -> dict[str, Any]:
    paragraph_indices, table_index = safe_body_indices(template)
    if len(paragraph_indices) < 2 or table_index is None:
        raise ValueError("template does not have enough safe body paragraphs/tables for smoke block replacement")
    paragraph_text = f"{product} is a planning low-additive-jitter LVDS clock buffer. DS_NEED_CONFIRM."
    if stress_long_text:
        stress_sentence = (
            "DS_COMPETITOR_REF DS_NEED_CONFIRM Planning draft text replacement. "
            "This paragraph is intentionally longer than the template source paragraph "
            "to exercise layout drift checks without rebuilding the document body. "
            "Use this mode only when you want the smoke test to expose overflow, page-count drift, "
            "or poor content-length handling."
        )
        paragraph_text = " ".join([stress_sentence] * 12)
    return {
        "paragraphs": [
            {
                "index": paragraph_indices[0],
                "text": "DESCRIPTION",
            },
            {
                "index": paragraph_indices[1],
                "text": paragraph_text,
            },
        ],
        "tables": [
            {
                "index": table_index,
                "rows": [
                    ["Parameter", "Target", "Status"],
                    ["Outputs", "4 LVDS pairs", "DS_NEED_CONFIRM"],
                    ["Package", "16-pin VQFN", "DS_COMPETITOR_REF"],
                ],
            }
        ],
    }


def export_pdf(docx: Path, pdf: Path) -> dict[str, Any]:
    try:
        import pythoncom
        import win32com.client

        pythoncom.CoInitialize()
        word = win32com.client.DispatchEx("Word.Application")
        word.Visible = False
        word.DisplayAlerts = 0
        doc = None
        try:
            doc = word.Documents.Open(
                str(docx.resolve()),
                ConfirmConversions=False,
                ReadOnly=False,
                AddToRecentFiles=False,
                NoEncodingDialog=True,
            )
            pdf.parent.mkdir(parents=True, exist_ok=True)
            doc.ExportAsFixedFormat(str(pdf.resolve()), 17)
        finally:
            if doc is not None:
                doc.Close(False)
            word.Quit()
            pythoncom.CoUninitialize()
        return {"status": "exported", "pdf": str(pdf)}
    except Exception as exc:  # noqa: BLE001
        return {"status": "not-run", "error": str(exc), "pdf": str(pdf)}


def non_white_ratio(samples: bytes, stride: int = 60) -> float:
    checked = 0
    non_white = 0
    for index in range(0, len(samples), 3 * stride):
        pixel = samples[index : index + 3]
        if len(pixel) < 3:
            continue
        checked += 1
        if any(channel < 245 for channel in pixel):
            non_white += 1
    return non_white / checked if checked else 0.0


def render_and_measure(template_pdf: Path, output_pdf: Path, out_dir: Path, max_page_delta: int) -> dict[str, Any]:
    import fitz

    out_dir.mkdir(parents=True, exist_ok=True)
    template_doc = fitz.open(template_pdf)
    output_doc = fitz.open(output_pdf)
    template_pages = len(template_doc)
    output_pages = len(output_doc)
    selected = sorted({1, 2, min(output_pages, 3), output_pages})
    rendered: list[dict[str, Any]] = []
    errors: list[str] = []

    if abs(output_pages - template_pages) > max_page_delta:
        errors.append(f"page count drifted: template={template_pages}, output={output_pages}")

    common_pages = min(template_pages, output_pages)
    for page_num in selected:
        if page_num < 1 or page_num > output_pages:
            continue
        output_page = output_doc[page_num - 1]
        template_page = template_doc[min(page_num, common_pages) - 1]
        output_rect = output_page.rect
        template_rect = template_page.rect
        if abs(output_rect.width - template_rect.width) > 1 or abs(output_rect.height - template_rect.height) > 1:
            errors.append(f"page size drifted at page {page_num}")
        pix = output_page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5), alpha=False)
        image_path = out_dir / f"page-{page_num:02d}.png"
        pix.save(image_path)
        ratio = non_white_ratio(pix.samples)
        if ratio < 0.002:
            errors.append(f"rendered page {page_num} looks blank")
        rendered.append({"page": page_num, "image": str(image_path), "non_white_ratio": ratio})

    return {
        "status": "passed" if not errors else "failed",
        "template_page_count": template_pages,
        "output_page_count": output_pages,
        "rendered": rendered,
        "errors": errors,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Smoke-test template-copy DOCX replacement scripts.")
    parser.add_argument("--template", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, default=Path("tmp/script-tests/docx-replace-smoke"))
    parser.add_argument("--product", default="NCS25D31B")
    parser.add_argument("--company", default="NCS")
    parser.add_argument("--title", default="Low Additive Jitter LVDS Buffer")
    parser.add_argument("--skip-pdf", action="store_true")
    parser.add_argument("--max-page-delta", type=int, default=0)
    parser.add_argument("--max-text-ratio", type=float, default=3.0)
    parser.add_argument("--max-added-chars", type=int, default=800)
    parser.add_argument("--stress-long-text", action="store_true")
    args = parser.parse_args(argv)

    run_dir = args.out_dir / datetime.now().strftime("%Y%m%d-%H%M%S")
    logs_dir = run_dir / "logs"
    reports_dir = run_dir / "reports"
    artifacts_dir = run_dir / "artifacts"
    run_dir.mkdir(parents=True, exist_ok=False)

    replacements = default_replacements(args.product, args.company, args.title)
    replacements_json = run_dir / "replacements.json"
    write_json(replacements_json, replacements)

    block_ops = make_block_ops(args.template, args.product, args.stress_long_text)
    block_ops_json = run_dir / "block-ops.json"
    write_json(block_ops_json, block_ops)
    length_budget = check_block_length_budget(
        args.template,
        block_ops,
        max_text_ratio=args.max_text_ratio,
        max_added_chars=args.max_added_chars,
    )
    write_json(reports_dir / "00-length-budget.json", length_budget)

    asset_diff_json = run_dir / "asset-diff-comments.json"
    write_json(
        asset_diff_json,
        {
            "accepted_reductions": [
                {
                    "resource": "template comments",
                    "status": "accepted-with-notes",
                    "reason": "Comments are stripped after replacement smoke tests so template instructions do not remain in output.",
                }
            ]
        },
    )

    stage1 = artifacts_dir / "01-text-replaced.docx"
    stage2 = artifacts_dir / "02-block-replaced.docx"
    stage3 = artifacts_dir / "03-comments-stripped.docx"

    steps: list[dict[str, Any]] = []
    steps.append(
        run_command(
            py_command(
                "patch_docx_text.py",
                "--template",
                args.template,
                "--output",
                stage1,
                "--replacements-json",
                replacements_json,
                "--report",
                reports_dir / "01-text-replaced.json",
            ),
            logs_dir,
            "01-text-replaced",
        )
    )
    steps.append(
        run_command(
            py_command(
                "check_docx_template_fidelity.py",
                "--template",
                args.template,
                "--output",
                stage1,
                "--format",
                "json",
            ),
            logs_dir,
            "02-fidelity-after-text",
        )
    )
    steps.append(
        run_command(
            py_command(
                "patch_docx_blocks.py",
                "--template",
                stage1,
                "--operations",
                block_ops_json,
                "--output",
                stage2,
                "--report",
                reports_dir / "03-block-replaced.json",
            ),
            logs_dir,
            "03-block-replaced",
        )
    )
    steps.append(
        run_command(
            py_command(
                "check_docx_template_fidelity.py",
                "--template",
                args.template,
                "--output",
                stage2,
                "--format",
                "json",
            ),
            logs_dir,
            "04-fidelity-after-blocks",
        )
    )
    steps.append(
        run_command(
            py_command(
                "strip_docx_comments.py",
                "--input",
                stage2,
                "--output",
                stage3,
                "--report",
                reports_dir / "05-comments-stripped.json",
            ),
            logs_dir,
            "05-comments-stripped",
        )
    )
    steps.append(
        run_command(
            py_command(
                "check_docx_template_fidelity.py",
                "--template",
                args.template,
                "--output",
                stage3,
                "--asset-diff",
                asset_diff_json,
                "--format",
                "json",
            ),
            logs_dir,
            "06-fidelity-final",
        )
    )

    residual_terms = [item["old"] for item in replacements]
    residuals = find_residuals(stage3, residual_terms)
    residual_payload = {"status": "passed" if not residuals else "failed", "residuals": residuals}
    write_json(reports_dir / "07-residual-check.json", residual_payload)
    toc_bookmarks = check_toc_bookmarks(stage3)
    write_json(reports_dir / "07b-toc-bookmarks.json", toc_bookmarks)

    visual_payload: dict[str, Any] = {"status": "not-run", "reason": "--skip-pdf was set"}
    if not args.skip_pdf:
        template_pdf = artifacts_dir / "template.pdf"
        output_pdf = artifacts_dir / "output.pdf"
        template_export = export_pdf(args.template, template_pdf)
        output_export = export_pdf(stage3, output_pdf)
        if template_export["status"] == "exported" and output_export["status"] == "exported":
            visual_payload = render_and_measure(template_pdf, output_pdf, artifacts_dir / "visual", args.max_page_delta)
            visual_payload["template_pdf"] = str(template_pdf)
            visual_payload["output_pdf"] = str(output_pdf)
        else:
            visual_payload = {"status": "not-run", "template_export": template_export, "output_export": output_export}
    write_json(reports_dir / "08-render-check.json", visual_payload)

    hard_failures: list[str] = []
    for step in steps:
        if step["returncode"] != 0:
            hard_failures.append(f"{step['name']} failed with exit code {step['returncode']}")
    final_fidelity = load_fidelity_report(logs_dir / "06-fidelity-final.stdout.txt")
    if final_fidelity.get("status") not in {"passed", "accepted-with-notes"}:
        hard_failures.append("final fidelity did not pass or reach accepted-with-notes")
    if residual_payload["status"] != "passed":
        hard_failures.append("residual old terms remain after replacement")
    if toc_bookmarks["status"] != "passed":
        hard_failures.append(f"TOC references missing bookmarks: {', '.join(toc_bookmarks['missing'])}")
    if length_budget["status"] != "passed":
        hard_failures.extend(length_budget["errors"])
    if visual_payload.get("status") == "failed":
        hard_failures.extend(visual_payload.get("errors", []))

    summary = {
        "status": "passed" if not hard_failures else "failed",
        "run_dir": str(run_dir),
        "template": str(args.template),
        "final_docx": str(stage3),
        "steps": steps,
        "residual_check": residual_payload,
        "toc_bookmarks": toc_bookmarks,
        "length_budget": length_budget,
        "visual_check": visual_payload,
        "hard_failures": hard_failures,
    }
    write_json(run_dir / "summary.json", summary)
    lines = [
        "# DOCX Replacement Smoke Test",
        "",
        f"- Status: {summary['status']}",
        f"- Template: {args.template}",
        f"- Final DOCX: {stage3}",
        f"- Residual check: {residual_payload['status']}",
        f"- Render check: {visual_payload.get('status')}",
        "",
        "## Hard Failures",
    ]
    if hard_failures:
        lines.extend(f"- {item}" for item in hard_failures)
    else:
        lines.append("- None")
    (run_dir / "summary.md").write_text("\n".join(lines), encoding="utf-8")

    print(json.dumps({"status": summary["status"], "run_dir": str(run_dir), "final_docx": str(stage3)}, ensure_ascii=False, indent=2))
    return 0 if summary["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
