#! python3
"""Normalize datasheet_model metadata and template inventory before DOCX rendering."""

from __future__ import annotations

import argparse
import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from check_docx_template_fidelity import summarize_docx
from extract_template_manifest import build_manifest


def load_model(path: Path) -> tuple[dict[str, Any], bool]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("model root must be a mapping")
    nested = "datasheet_model" in data
    model = data["datasheet_model"] if nested else data
    if not isinstance(model, dict):
        raise ValueError("datasheet_model must be a mapping")
    return data, nested


def ensure_dict(parent: dict[str, Any], key: str) -> dict[str, Any]:
    value = parent.get(key)
    if not isinstance(value, dict):
        value = {}
        parent[key] = value
    return value


def resource_inventory(template: Path) -> dict[str, int]:
    summary = summarize_docx(template)
    return {
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


def load_manifest(path: Path | None, template: Path) -> dict[str, Any]:
    if path:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("template manifest must be a mapping")
        return data
    return build_manifest(template)


def merge_non_blank(base: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
    merged = deepcopy(base)
    for key, value in overlay.items():
        if value in (None, "", [], {}):
            continue
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = merge_non_blank(merged[key], value)
        else:
            merged[key] = value
    return merged


def merge_manifest(generated: dict[str, Any], existing: dict[str, Any]) -> dict[str, Any]:
    merged = merge_non_blank(generated, existing)
    for key in ("anchors", "body", "paragraphs", "tables", "sample_rows", "comments"):
        generated_value = generated.get(key)
        existing_value = existing.get(key)
        if generated_value and (not existing_value or type(existing_value) is not type(generated_value)):
            merged[key] = generated_value
    return merged


def fill_slot(slot: str, target: str, source: str, status: str = "confirmed input gate") -> dict[str, str]:
    return {
        "slot": slot,
        "operation": "fill",
        "target": target,
        "source": source,
        "status": status,
    }


def ensure_fill_slots(model: dict[str, Any], company: str, product: str, release_date: str) -> None:
    slot_map = model.get("slot_map")
    if not isinstance(slot_map, list):
        slot_map = []
        model["slot_map"] = slot_map

    existing = {item.get("slot") for item in slot_map if isinstance(item, dict)}
    required = [
        fill_slot("cover.product_name", product, "input_gate.product_name"),
        fill_slot("cover.company", company, "input_gate.company"),
        fill_slot("metadata.release_date", release_date, "input_gate.release_date"),
        fill_slot("header.product_name", product, "input_gate.product_name"),
        fill_slot("header.company", company, "input_gate.company"),
        fill_slot("footer.company", company, "input_gate.company"),
        fill_slot("legal_notice.subject", company, "input_gate.company", "DS_NEED_CONFIRM if boilerplate unavailable"),
    ]
    for item in required:
        if item["slot"] not in existing:
            slot_map.insert(0, item)


def normalize(
    data: dict[str, Any],
    *,
    nested: bool,
    template: Path,
    manifest_path: Path | None,
    company: str,
    product: str,
    release_date: str,
) -> dict[str, Any]:
    output = deepcopy(data)
    model = output["datasheet_model"] if nested else output

    metadata = ensure_dict(model, "metadata")
    metadata["company"] = company
    if product:
        metadata["product_name"] = product
    if release_date:
        metadata["release_date"] = release_date

    fixed_layout = ensure_dict(model, "fixed_layout")
    existing_manifest = ensure_dict(fixed_layout, "template_manifest")
    generated_manifest = load_manifest(manifest_path, template)
    if "resource_inventory" not in generated_manifest:
        generated_manifest["resource_inventory"] = resource_inventory(template)
    fixed_layout["template_manifest"] = merge_manifest(generated_manifest, existing_manifest)

    fixed_layout["header_footer"] = {
        "subject": company,
        "replacement_policy": "Preserve template header/footer relationships and layout; replace company/legal/product text only.",
        "status": "confirmed input gate",
    }
    fixed_layout["legal_notice"] = {
        "subject": company,
        "replacement_policy": "Preserve template legal layout; replace legal subject with confirmed company. Mark DS_NEED_CONFIRM if exact boilerplate is unavailable.",
        "status": "confirmed input gate; boilerplate may require legal review",
    }

    ensure_fill_slots(model, company, metadata.get("product_name", product), metadata.get("release_date", release_date))
    return output


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Normalize ncs-datasheet-gen model gates.")
    parser.add_argument("--model", type=Path, required=True, help="Input datasheet_model JSON")
    parser.add_argument("--template", type=Path, required=True, help="Template DOCX used for resource_inventory")
    parser.add_argument("--manifest", type=Path, help="Optional pre-extracted template_manifest JSON")
    parser.add_argument("--output", type=Path, required=True, help="Normalized output JSON")
    parser.add_argument("--company", required=True, help="Confirmed company/legal subject")
    parser.add_argument("--product", default="", help="Confirmed product name")
    parser.add_argument("--release-date", default="", help="Confirmed release date")
    parser.add_argument("--report", type=Path, help="Optional JSON report path")
    args = parser.parse_args(argv)

    try:
        data, nested = load_model(args.model)
        normalized = normalize(
            data,
            nested=nested,
            template=args.template,
            manifest_path=args.manifest,
            company=args.company,
            product=args.product,
            release_date=args.release_date,
        )
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(normalized, ensure_ascii=False, indent=2), encoding="utf-8")
        payload = {
            "status": "normalized",
            "model": str(args.model),
            "template": str(args.template),
            "output": str(args.output),
            "company": args.company,
            "product": args.product,
        }
    except Exception as exc:  # noqa: BLE001 - command line should report compact failures.
        payload = {"status": "failed", "errors": [str(exc)]}

    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["status"] == "normalized" else 1


if __name__ == "__main__":
    raise SystemExit(main())
