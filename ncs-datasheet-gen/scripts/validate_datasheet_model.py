#! python3
"""Validate an ncs-datasheet-gen datasheet_model file."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


MARKING_CODES = {
    "DS_TBD",
    "DS_NEED_CONFIRM",
    "DS_COMPETITOR_REF",
    "DS_BELOW_COMPETITOR",
    "DS_MISSING_HISTORY",
    "DS_PLACEHOLDER_IMAGE",
    "DS_UNVERIFIED_SPEC",
}

SLOT_OPERATIONS = {
    "fill",
    "replace_block",
    "insert_after_anchor",
}

UNCONFIRMED_IDENTITY_TOKENS = {
    "inherited from template",
    "inherit template",
    "template company",
    "template legal",
    "unknown",
    "tbd",
}

NCS_CONFLICTING_COMPANY_TOKENS = {
    "joulwatt",
    "joul watt",
}

REQUIRED_TEMPLATE_MANIFEST_FIELDS = {
    "sections",
    "headers_footers",
    "toc_fields",
    "page_roles",
    "replaceable_blocks",
    "anchors",
    "sample_rows",
    "protected_blocks",
    "resource_inventory",
}

REQUIRED_NON_EMPTY_TEMPLATE_FIELDS = {
    "sections",
    "page_roles",
}

REQUIRED_METADATA = [
    "product_name",
    "document_title",
    "status",
    "company",
    "competitor",
]

STRUCTURED_SECTIONS_REQUIRING_SOURCE = {
    "ordering",
    "device_information",
    "device_comparison",
    "pins",
    "absolute_maximum_ratings",
    "esd_ratings",
    "recommended_operating_conditions",
    "thermal_information",
    "electrical_characteristics",
    "timing_characteristics",
    "control_tables",
    "typical_characteristics",
    "package_information",
    "tape_and_reel",
    "revision_history",
    "registers",
}

PARAMETER_SECTIONS = {
    "absolute_maximum_ratings",
    "esd_ratings",
    "recommended_operating_conditions",
    "thermal_information",
    "electrical_characteristics",
    "timing_characteristics",
    "typical_characteristics",
}


def load_model(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() in {".yaml", ".yml"}:
        try:
            import yaml  # type: ignore
        except ImportError as exc:
            raise SystemExit("PyYAML is required to read YAML models. Install scripts/requirements.txt.") from exc
        data = yaml.safe_load(text)
    else:
        data = json.loads(text)
    if not isinstance(data, dict):
        raise ValueError("model root must be a mapping")
    if "datasheet_model" in data:
        model = data["datasheet_model"]
    else:
        model = data
    if not isinstance(model, dict):
        raise ValueError("datasheet_model must be a mapping")
    return model


def is_blank(value: Any) -> bool:
    return value is None or value == "" or value == []


def iter_items(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    if isinstance(value, dict):
        return [value]
    return []


def check_source(item: dict[str, Any], path: str, errors: list[str]) -> None:
    if is_blank(item.get("source")):
        errors.append(f"{path}.source is required for structured facts")


def check_parameter(item: dict[str, Any], path: str, errors: list[str], warnings: list[str]) -> None:
    if is_blank(item.get("parameter")) and is_blank(item.get("name")):
        errors.append(f"{path}.parameter is required")
    if is_blank(item.get("unit")):
        errors.append(f"{path}.unit is required")
    if all(is_blank(item.get(key)) for key in ("min", "typ", "max", "value")):
        errors.append(f"{path} must include at least one of min, typ, max, or value")
    if is_blank(item.get("test_condition")):
        errors.append(f"{path}.test_condition is required")
    values = [item.get("min"), item.get("typ"), item.get("max")]
    if all(isinstance(value, (int, float)) for value in values if value is not None):
        present = [value for value in values if value is not None]
        if present != sorted(present):
            warnings.append(f"{path} min/typ/max order should be reviewed")


def check_pins(pins: Any, errors: list[str], warnings: list[str]) -> None:
    seen_numbers: dict[str, int] = {}
    seen_names: dict[str, int] = {}
    for index, pin in enumerate(iter_items(pins)):
        path = f"structured_sections.pins[{index}]"
        check_source(pin, path, errors)
        for field in ("pin_number", "pin_name", "pin_type", "function"):
            if is_blank(pin.get(field)):
                errors.append(f"{path}.{field} is required")
        number = str(pin.get("pin_number", "")).strip()
        name = str(pin.get("pin_name", "")).strip().upper()
        if number:
            if number in seen_numbers:
                errors.append(f"{path}.pin_number duplicates structured_sections.pins[{seen_numbers[number]}]")
            seen_numbers[number] = index
        if name:
            if name in seen_names and name not in {"GND", "VSS", "NC", "DNC", "RESERVED"}:
                warnings.append(f"{path}.pin_name duplicates structured_sections.pins[{seen_names[name]}]")
            seen_names[name] = index
    if pins and not any(str(pin.get("pin_name", "")).upper() in {"GND", "VSS"} for pin in iter_items(pins)):
        warnings.append("structured_sections.pins should include at least one ground pin or explain the exception")


def check_markings(markings: Any, warnings: list[str]) -> None:
    if not isinstance(markings, dict):
        return
    for group_name, items in markings.items():
        for index, item in enumerate(iter_items(items)):
            code = item.get("code") or item.get("marking")
            if code and code not in MARKING_CODES:
                warnings.append(f"markings.{group_name}[{index}] uses unknown marking code {code!r}")
            if is_blank(item.get("reason")) and is_blank(item.get("description")):
                warnings.append(f"markings.{group_name}[{index}] should include reason or description")


def check_template_manifest(fixed_layout: Any, errors: list[str], warnings: list[str]) -> None:
    if not isinstance(fixed_layout, dict):
        errors.append("fixed_layout is required")
        return

    manifest = fixed_layout.get("template_manifest")
    if not isinstance(manifest, dict):
        errors.append("fixed_layout.template_manifest is required")
        return

    for field in sorted(REQUIRED_TEMPLATE_MANIFEST_FIELDS):
        if field not in manifest:
            errors.append(f"fixed_layout.template_manifest.{field} is required")
        elif field in REQUIRED_NON_EMPTY_TEMPLATE_FIELDS and is_blank(manifest.get(field)):
            errors.append(f"fixed_layout.template_manifest.{field} must not be empty")

    if is_blank(manifest.get("headers_footers")):
        warnings.append("fixed_layout.template_manifest.headers_footers is empty; confirm template has no header/footer")
    if is_blank(manifest.get("replaceable_blocks")) and is_blank(manifest.get("anchors")):
        warnings.append("template_manifest should include replaceable_blocks or anchors before DOCX generation")


def text_contains(value: Any, tokens: set[str]) -> bool:
    text = json.dumps(value, ensure_ascii=False).lower() if isinstance(value, (dict, list)) else str(value).lower()
    return any(token in text for token in tokens)


def check_identity_policy(metadata: dict[str, Any], fixed_layout: Any, errors: list[str], warnings: list[str]) -> None:
    company = metadata.get("company")
    product_name = str(metadata.get("product_name", "")).strip()
    if text_contains(company, UNCONFIRMED_IDENTITY_TOKENS):
        errors.append("metadata.company must be explicitly confirmed; do not inherit company/legal identity from the template")

    if product_name.upper().startswith("NCS") and text_contains(company, NCS_CONFLICTING_COMPANY_TOKENS):
        errors.append("metadata.company conflicts with NCS product identity; confirm company/logo/legal subject before generation")

    if not isinstance(fixed_layout, dict):
        return
    for field in ("header_footer", "legal_notice"):
        value = fixed_layout.get(field)
        if text_contains(value, {"inherit template", "inherited from template"}):
            errors.append(f"fixed_layout.{field} must name the confirmed output subject, not blindly inherit template identity")
        elif text_contains(value, {"inherit"}):
            warnings.append(f"fixed_layout.{field} uses inherit wording; confirm this does not copy the wrong company/legal subject")


def check_slot_map(slot_map: Any, errors: list[str], warnings: list[str]) -> None:
    if not isinstance(slot_map, list) or not slot_map:
        errors.append("slot_map is required and must contain at least one template operation")
        return

    seen_slots: set[str] = set()
    has_fill = False
    has_replace_or_insert = False
    for index, item in enumerate(slot_map):
        path = f"slot_map[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{path} must be a mapping")
            continue

        for field in ("slot", "operation", "target", "source"):
            if is_blank(item.get(field)):
                errors.append(f"{path}.{field} is required")

        slot = str(item.get("slot", "")).strip()
        if slot:
            if slot in seen_slots:
                errors.append(f"{path}.slot duplicates an earlier slot: {slot}")
            seen_slots.add(slot)

        operation = item.get("operation")
        if operation and operation not in SLOT_OPERATIONS:
            errors.append(f"{path}.operation {operation!r} is not allowed; use one of {sorted(SLOT_OPERATIONS)}")
        if operation == "fill":
            has_fill = True
        if operation in {"replace_block", "insert_after_anchor"}:
            has_replace_or_insert = True

    if not has_fill:
        errors.append("slot_map must include fill operations for short template fields such as product, status, date, header, footer, or company")
    if not has_replace_or_insert:
        warnings.append("slot_map has only fill operations; confirm the template needs no block replacement or controlled insertion")


def validate(model: dict[str, Any]) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    metadata = model.get("metadata")
    if not isinstance(metadata, dict):
        errors.append("metadata is required")
        metadata = {}
    for field in REQUIRED_METADATA:
        if is_blank(metadata.get(field)):
            errors.append(f"metadata.{field} is required")

    check_template_manifest(model.get("fixed_layout"), errors, warnings)
    check_identity_policy(metadata, model.get("fixed_layout"), errors, warnings)
    check_slot_map(model.get("slot_map"), errors, warnings)

    structured = model.get("structured_sections")
    if not isinstance(structured, dict):
        errors.append("structured_sections is required")
        structured = {}

    check_pins(structured.get("pins"), errors, warnings)

    for section_name, section_value in structured.items():
        if section_name not in STRUCTURED_SECTIONS_REQUIRING_SOURCE:
            continue
        for index, item in enumerate(iter_items(section_value)):
            path = f"structured_sections.{section_name}[{index}]"
            check_source(item, path, errors)
            if section_name in PARAMETER_SECTIONS:
                check_parameter(item, path, errors, warnings)

    check_markings(model.get("markings"), warnings)
    return errors, warnings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate ncs-datasheet-gen datasheet_model JSON/YAML.")
    parser.add_argument("model", type=Path, help="Path to datasheet_model.json or datasheet_model.yaml")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")
    args = parser.parse_args(argv)

    try:
        model = load_model(args.model)
        errors, warnings = validate(model)
    except Exception as exc:  # noqa: BLE001 - CLI should surface parse failures cleanly.
        errors = [f"failed to load model: {exc}"]
        warnings = []

    payload = {
        "status": "passed" if not errors else "failed",
        "errors": errors,
        "warnings": warnings,
    }

    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"status: {payload['status']}")
        for label in ("errors", "warnings"):
            for message in payload[label]:
                print(f"{label[:-1]}: {message}")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
