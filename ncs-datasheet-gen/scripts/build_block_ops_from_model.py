#! python3
"""Build manifest-driven DOCX block operations from a normalized datasheet_model."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


def load_model(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    model = data.get("datasheet_model", data)
    if not isinstance(model, dict):
        raise ValueError("datasheet_model must be a mapping")
    return model


def compact(text: Any, limit: int = 170) -> str:
    text = re.sub(r"\s+", " ", "" if text is None else str(text)).strip()
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


def iter_items(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    if isinstance(value, dict):
        return [value]
    return []


def section_items(model: dict[str, Any], section: str) -> list[dict[str, Any]]:
    structured = model.get("structured_sections")
    if not isinstance(structured, dict):
        return []
    return iter_items(structured.get(section))


def semi_items(model: dict[str, Any], section: str) -> list[str]:
    semi = model.get("semi_structured_sections")
    if not isinstance(semi, dict):
        return []
    value = semi.get(section)
    if isinstance(value, list):
        return [compact(item, 500) for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [compact(value, 500)]
    return []


def template_manifest(model: dict[str, Any]) -> dict[str, Any]:
    fixed_layout = model.get("fixed_layout")
    if not isinstance(fixed_layout, dict):
        raise ValueError("fixed_layout.template_manifest is required; run normalize_datasheet_model.py first")
    manifest = fixed_layout.get("template_manifest")
    if not isinstance(manifest, dict):
        raise ValueError("fixed_layout.template_manifest is required; run normalize_datasheet_model.py first")
    return manifest


def normalized_text(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def anchor_matches(text: str, tokens: tuple[str, ...]) -> bool:
    folded = normalized_text(text)
    return all(normalized_text(token) in folded for token in tokens)


def anchors_matching(manifest: dict[str, Any], *tokens: str) -> list[dict[str, Any]]:
    anchors = manifest.get("anchors")
    if not isinstance(anchors, dict):
        return []
    matches = []
    for key, value in anchors.items():
        if not isinstance(value, dict):
            continue
        text = str(value.get("text", ""))
        if anchor_matches(text, tokens):
            item = dict(value)
            item["anchor"] = key
            matches.append(item)
    return sorted(matches, key=lambda item: int(item.get("paragraph_index", 0)))


def first_anchor(manifest: dict[str, Any], *tokens: str) -> dict[str, Any] | None:
    matches = anchors_matching(manifest, *tokens)
    return matches[0] if matches else None


def first_anchor_after(manifest: dict[str, Any], paragraph_index: int, *tokens: str) -> dict[str, Any] | None:
    for anchor in anchors_matching(manifest, *tokens):
        if int(anchor.get("paragraph_index", -1)) > paragraph_index:
            return anchor
    return None


def body_sequence(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    body = manifest.get("body")
    return body if isinstance(body, list) else []


def paragraph_infos(manifest: dict[str, Any]) -> dict[int, dict[str, Any]]:
    rows = manifest.get("paragraphs")
    if not isinstance(rows, list):
        return {}
    return {int(item["index"]): item for item in rows if isinstance(item, dict) and "index" in item}


def table_infos(manifest: dict[str, Any]) -> dict[int, dict[str, Any]]:
    rows = manifest.get("tables")
    if not isinstance(rows, list):
        return {}
    return {int(item["index"]): item for item in rows if isinstance(item, dict) and "index" in item}


def table_column_count(manifest: dict[str, Any], table_index: int | None) -> int:
    if table_index is None:
        return 0
    try:
        return int(table_infos(manifest).get(table_index, {}).get("cols", 0))
    except (TypeError, ValueError):
        return 0


def table_after_paragraph(manifest: dict[str, Any], paragraph_index: int) -> int | None:
    info = paragraph_infos(manifest).get(paragraph_index)
    if not info:
        return None
    start_child = int(info.get("child_index", -1))
    for item in body_sequence(manifest):
        if int(item.get("child_index", -1)) <= start_child:
            continue
        if item.get("kind") == "paragraph" and int(item.get("index", -1)) > paragraph_index:
            text = str(item.get("text", "")).strip()
            if text and text.upper() == text and len(text) > 2:
                return None
        if item.get("kind") == "table":
            return int(item["index"])
    return None


def tables_after_paragraph(manifest: dict[str, Any], paragraph_index: int) -> list[int]:
    info = paragraph_infos(manifest).get(paragraph_index)
    if not info:
        return []
    start_child = int(info.get("child_index", -1))
    indexes: list[int] = []
    for item in body_sequence(manifest):
        if int(item.get("child_index", -1)) <= start_child:
            continue
        if item.get("kind") == "table":
            indexes.append(int(item["index"]))
    return indexes


def paragraph_after(manifest: dict[str, Any], paragraph_index: int, offset: int) -> int | None:
    paragraphs = sorted(paragraph_infos(manifest))
    try:
        pos = paragraphs.index(paragraph_index)
    except ValueError:
        return None
    target = pos + offset
    if 0 <= target < len(paragraphs):
        return paragraphs[target]
    return None


def blank_visual_paragraphs_between(manifest: dict[str, Any], start: int, end: int) -> list[int]:
    infos = paragraph_infos(manifest)
    rows = []
    for index in sorted(infos):
        if start < index < end:
            info = infos[index]
            if not str(info.get("text", "")).strip() and (
                info.get("has_drawing")
                or info.get("has_legacy_picture")
                or info.get("has_ole_object")
            ):
                rows.append(index)
    return rows


def add_paragraph(ops: dict[str, Any], index: int | None, text: str, source_slot: str, preserve_visuals: bool | None = None) -> None:
    if index is None:
        return
    item: dict[str, Any] = {"index": index, "text": text, "source_slot": source_slot}
    if preserve_visuals is not None:
        item["preserve_visuals"] = preserve_visuals
    ops["paragraphs"].append(item)


def add_table(ops: dict[str, Any], index: int | None, rows: list[list[Any]], source_slot: str) -> None:
    if index is None:
        return
    ops["tables"].append({"index": index, "rows": rows, "source_slot": source_slot})


def has_visual_payload(info: dict[str, Any]) -> bool:
    return bool(info.get("has_drawing") or info.get("has_legacy_picture") or info.get("has_ole_object"))


def metadata_value(model: dict[str, Any], key: str, default: str = "") -> str:
    metadata = model.get("metadata")
    if isinstance(metadata, dict):
        value = metadata.get(key)
        if value not in (None, ""):
            return str(value)
    return default


def package_label(model: dict[str, Any]) -> str:
    for item in section_items(model, "package_information") + section_items(model, "device_information") + section_items(model, "ordering"):
        for key in ("package", "package_name", "name", "description"):
            value = item.get(key)
            if value not in (None, ""):
                return compact(value, 80)
    metadata = model.get("metadata")
    if isinstance(metadata, dict):
        target_policy = metadata.get("target_policy")
        if isinstance(target_policy, dict):
            value = target_policy.get("pin_to_pin_target") or target_policy.get("package_policy")
            if value:
                return compact(value, 80)
    return "Target package"


def pin_lookup(model: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(pin.get("pin_number", "")).upper(): pin
        for pin in section_items(model, "pins")
        if pin.get("pin_number") not in (None, "")
    }


def pin_label(pins: dict[str, dict[str, Any]], number: int | str) -> str:
    key = str(number).upper()
    name = pins.get(key, {}).get("pin_name", "DS_TBD")
    return f"{key} {name}"


def sorted_numeric_pin_numbers(pins: dict[str, dict[str, Any]]) -> list[int]:
    values = []
    for key in pins:
        if key.isdigit():
            values.append(int(key))
    return sorted(values)


def build_pin_configuration_rows(model: dict[str, Any]) -> list[list[Any]]:
    pins = pin_lookup(model)
    product = metadata_value(model, "product_name", "Device")
    package = package_label(model)
    status = "DS_COMPETITOR_REF DS_PLACEHOLDER_IMAGE DS_NEED_CONFIRM"
    numeric = sorted_numeric_pin_numbers(pins)
    if len(numeric) == 16 and numeric == list(range(1, 17)):
        center = f"{package} / Thermal Pad / DAP: GND"
        return [
            ["", pin_label(pins, 12), pin_label(pins, 11), pin_label(pins, 10), pin_label(pins, 9), ""],
            [pin_label(pins, 13), "", "", "", "", pin_label(pins, 8)],
            [pin_label(pins, 14), "", center, "", "", pin_label(pins, 7)],
            [pin_label(pins, 15), "", "", "", "", pin_label(pins, 6)],
            [pin_label(pins, 16), "", "", "", "", pin_label(pins, 5)],
            ["", pin_label(pins, 1), pin_label(pins, 2), pin_label(pins, 3), pin_label(pins, 4), ""],
            ["Figure", f"{product} target pin configuration: {package} Top View", "", "", "", status],
        ]
    rows = [["Pin", "Name", "Type", "Status"]]
    for number in numeric:
        pin = pins[str(number)]
        rows.append([number, pin.get("pin_name", ""), pin.get("pin_type", ""), pin.get("status", status)])
    if "DAP" in pins:
        pin = pins["DAP"]
        rows.append(["DAP", pin.get("pin_name", "DAP"), pin.get("pin_type", ""), pin.get("status", status)])
    rows.append(["Figure", f"{product} target pin configuration: {package}", "", status])
    return rows


def value_text(item: dict[str, Any]) -> str:
    values = []
    for key in ("min", "typ", "max", "value"):
        value = item.get(key)
        if value not in (None, ""):
            values.append(f"{key.upper()}={value}")
    unit = item.get("unit", "")
    return " / ".join(values or ["DS_TBD"]) + (f" {unit}" if unit else "")


def pin_rows(model: dict[str, Any], column_count: int = 4) -> list[list[Any]]:
    if column_count <= 3:
        rows = [["Pin", "Name", "Description"]]
        for pin in section_items(model, "pins"):
            pin_type = compact(pin.get("pin_type", ""), 20)
            function = compact(pin.get("function", ""), 110)
            description = f"{pin_type}. {function}" if pin_type and function else function or pin_type
            rows.append([
                pin.get("pin_number", ""),
                pin.get("pin_name", ""),
                description,
            ])
        return rows

    rows = [["Pin", "Name", "Type", "Description"]]
    for pin in section_items(model, "pins"):
        rows.append([
            pin.get("pin_number", ""),
            pin.get("pin_name", ""),
            pin.get("pin_type", ""),
            compact(pin.get("function", ""), 95),
        ])
    return rows


def order_rows(model: dict[str, Any]) -> list[list[Any]]:
    rows = [["DEVICE", "PACKAGE", "TOP MARKING", "ENVIRONMENTAL", "SHIPPING METHOD", "MOQ"]]
    for item in section_items(model, "ordering")[:6]:
        rows.append([
            item.get("device", metadata_value(model, "product_name", "")),
            item.get("package", ""),
            item.get("top_marking", item.get("marking", "DS_TBD")),
            item.get("environmental", "DS_NEED_CONFIRM"),
            item.get("shipping_method", "DS_NEED_CONFIRM"),
            item.get("moq", "DS_TBD"),
        ])
    rows.append(["Notes", "Order information requires confirmation.", "DS_NEED_CONFIRM", "", "", ""])
    return rows


def device_rows(model: dict[str, Any]) -> list[list[Any]]:
    rows = [["DEVICE", "OPERATION MODE", "PACKAGE", "MSL", "STATUS"]]
    for item in section_items(model, "device_information")[:6]:
        rows.append([
            item.get("device", metadata_value(model, "product_name", "")),
            item.get("operation_mode", item.get("mode", "")),
            item.get("package", package_label(model)),
            item.get("msl", "DS_TBD"),
            item.get("status", "DS_NEED_CONFIRM"),
        ])
    return rows


def thermal_rows(model: dict[str, Any]) -> list[list[Any]]:
    package = package_label(model)
    rows = [["Thermal Metric", "Description", package, "Status", "Unit"]]
    items = section_items(model, "thermal_information")
    if not items:
        return rows + [["thetaJA", "Junction-to-ambient thermal resistance", "DS_TBD", "DS_NEED_CONFIRM", "degC/W"]]
    for item in items:
        rows.append([
            item.get("parameter", item.get("name", "")),
            item.get("description", ""),
            value_text(item),
            item.get("status", "DS_NEED_CONFIRM"),
            item.get("unit", ""),
        ])
    return rows


def electrical_rows(model: dict[str, Any]) -> list[list[Any]]:
    rows = [["Item", "Symbol/Name", "Condition", "Min", "Typ", "Max", "Unit", "Status"]]
    for section in ("electrical_characteristics", "timing_characteristics"):
        for item in section_items(model, section):
            rows.append([
                compact(item.get("parameter", item.get("name", "")), 45),
                compact(item.get("name", ""), 24),
                compact(item.get("test_condition", ""), 72),
                item.get("min", ""),
                item.get("typ", item.get("value", "")),
                item.get("max", ""),
                item.get("unit", ""),
                item.get("status", "DS_COMPETITOR_REF; DS_UNVERIFIED_SPEC; DS_NEED_CONFIRM"),
            ])
    return rows


def add_text_block(
    ops: dict[str, Any],
    manifest: dict[str, Any],
    heading_tokens: tuple[str, ...],
    title: str,
    texts: list[str],
    slot: str,
    *,
    stop_tokens: tuple[str, ...] | None = None,
    clear_remainder: bool = False,
    clear_visuals: bool = False,
) -> None:
    anchor = first_anchor(manifest, *heading_tokens)
    if not anchor:
        return
    heading_index = int(anchor["paragraph_index"])
    preserve_written_visuals = False if clear_visuals else None
    written = {heading_index}
    add_paragraph(ops, heading_index, title, slot, preserve_visuals=preserve_written_visuals)
    for offset, text in enumerate(texts, start=1):
        index = paragraph_after(manifest, heading_index, offset)
        if index is not None:
            written.add(index)
        add_paragraph(ops, index, compact(text, 230), slot, preserve_visuals=preserve_written_visuals)
    if not clear_remainder or not stop_tokens:
        return
    stop_anchor = first_anchor_after(manifest, heading_index, *stop_tokens)
    if not stop_anchor:
        return
    stop_index = int(stop_anchor["paragraph_index"])
    for index, info in sorted(paragraph_infos(manifest).items()):
        if heading_index < index < stop_index and index not in written and not info.get("has_field"):
            if has_visual_payload(info) and not clear_visuals:
                continue
            add_paragraph(ops, index, "", slot, preserve_visuals=False if clear_visuals else None)


def clear_pin_visual_examples(ops: dict[str, Any], manifest: dict[str, Any]) -> None:
    pin_descriptions = sorted(int(item["paragraph_index"]) for item in anchors_matching(manifest, "pin", "description"))
    for top_view in anchors_matching(manifest, "top", "view"):
        start = int(top_view["paragraph_index"])
        end = next((index for index in pin_descriptions if index > start), None)
        if end is None:
            continue
        for index in blank_visual_paragraphs_between(manifest, start, end):
            add_paragraph(ops, index, "", "pins.remove_template_pinout", preserve_visuals=False)


def build_heuristic_ops(model: dict[str, Any], manifest: dict[str, Any]) -> dict[str, Any]:
    ops: dict[str, Any] = {
        "paragraphs": [],
        "clear_paragraph_ranges": [],
        "replace_paragraph_ranges": [],
        "remove_visuals_in_ranges": [],
        "tables": [],
        "remove_tables": [],
        "insert_tables_after_paragraphs": [],
        "remove_empty_trailing_paragraphs": {"source_slot": "cleanup.trailing_blank_paragraphs"},
    }
    product = metadata_value(model, "product_name", "Device")
    company = metadata_value(model, "company", "Company")
    competitor = metadata_value(model, "competitor", "competitor")

    add_text_block(ops, manifest, ("description",), "DESCRIPTION", semi_items(model, "description")[:3], "front.description", stop_tokens=("features",), clear_remainder=True)
    add_text_block(ops, manifest, ("features",), "FEATURES", ["- " + item for item in semi_items(model, "features")[:15]], "front.features", stop_tokens=("applications",), clear_remainder=True)
    add_text_block(ops, manifest, ("applications",), "APPLICATIONS", ["- " + item for item in semi_items(model, "applications")[:8]], "front.applications", stop_tokens=("typical", "application"), clear_remainder=True)
    add_text_block(ops, manifest, ("typical", "application"), "TYPICAL APPLICATION", [
        "DS_PLACEHOLDER_IMAGE: Typical application diagram requires owned artwork or approved redraw. DS_COMPETITOR_REF DS_NEED_CONFIRM"
    ], "figures.typical_application", stop_tokens=("contents",), clear_remainder=True, clear_visuals=True)
    add_text_block(ops, manifest, ("functional", "description"), "FUNCTIONAL DESCRIPTION", semi_items(model, "functional_description")[:6], "body.functional_description")
    add_text_block(ops, manifest, ("application", "information"), "APPLICATION INFORMATION", semi_items(model, "application_information")[:5], "body.application_information")

    for tokens, title, rows, slot in [
        (("order", "information"), "ORDER INFORMATION", order_rows(model), "tables.ordering"),
        (("device", "information"), "DEVICE INFORMATION", device_rows(model), "tables.device_information"),
        (("thermal", "performance"), "THERMAL PERFORMANCE", thermal_rows(model), "tables.thermal_information"),
        (("electrical",), "ELECTRICAL CHARACTERISTICS", electrical_rows(model), "tables.electrical_characteristics"),
    ]:
        anchor = first_anchor(manifest, *tokens)
        if anchor:
            add_paragraph(ops, int(anchor["paragraph_index"]), title, slot)
            add_table(ops, table_after_paragraph(manifest, int(anchor["paragraph_index"])), rows, slot)

    pin_config = first_anchor(manifest, "pin", "configuration")
    pin_desc = first_anchor(manifest, "pin", "description")
    if pin_config:
        add_paragraph(ops, int(pin_config["paragraph_index"]), "PIN CONFIGURATION", "pins.pin_configuration")
        top_view = first_anchor(manifest, "top", "view")
        if top_view and int(top_view["paragraph_index"]) > int(pin_config["paragraph_index"]):
            add_paragraph(ops, int(top_view["paragraph_index"]), "TOP VIEW", "pins.pin_configuration")
            ops["insert_tables_after_paragraphs"].append({
                "index": int(top_view["paragraph_index"]),
                "rows": build_pin_configuration_rows(model),
                "source_slot": "pins.pin_configuration",
            })
            clear_pin_visual_examples(ops, manifest)
    if pin_desc:
        add_paragraph(ops, int(pin_desc["paragraph_index"]), "PIN DESCRIPTION", "pins.pin_description")
        pin_table_index = table_after_paragraph(manifest, int(pin_desc["paragraph_index"]))
        add_table(ops, pin_table_index, pin_rows(model, table_column_count(manifest, pin_table_index)), "pins.pin_description")

    for extra in anchors_matching(manifest, "pin", "configuration")[1:] + anchors_matching(manifest, "top", "view")[1:] + anchors_matching(manifest, "pin", "description")[1:]:
        paragraph_index = int(extra["paragraph_index"])
        add_paragraph(ops, paragraph_index, "", "pins.remove_template_example", preserve_visuals=False)
        table_index = table_after_paragraph(manifest, paragraph_index)
        if table_index is not None:
            ops["remove_tables"].append(table_index)

    ratings = section_items(model, "absolute_maximum_ratings")
    anchor = first_anchor(manifest, "absolute", "maximum")
    if anchor and ratings:
        add_paragraph(ops, int(anchor["paragraph_index"]), "ABSOLUTE MAXIMUM RATING", "tables.absolute_maximum_ratings")
        for offset, item in enumerate(ratings[:8], start=1):
            add_paragraph(
                ops,
                paragraph_after(manifest, int(anchor["paragraph_index"]), offset),
                f"{item.get('parameter', item.get('name', 'Parameter'))} ................................ {value_text(item)}",
                "tables.absolute_maximum_ratings",
            )

    anchor = first_anchor(manifest, "block", "diagram")
    if anchor:
        add_paragraph(ops, int(anchor["paragraph_index"]), "BLOCK DIAGRAM", "figures.block_diagram")
        add_paragraph(
            ops,
            paragraph_after(manifest, int(anchor["paragraph_index"]), 1),
            "DS_PLACEHOLDER_IMAGE: Functional block diagram requires owned artwork or approved redraw.",
            "figures.block_diagram",
        )

    anchor = first_anchor(manifest, "historical")
    if anchor:
        add_paragraph(
            ops,
            paragraph_after(manifest, int(anchor["paragraph_index"]), 1),
            f"Historical product facts are the company baseline. Any target content derived from {competitor} must keep DS_* review markings until confirmed.",
            "review.history_boundary",
        )

    anchor = first_anchor(manifest, "description")
    if anchor:
        add_paragraph(
            ops,
            paragraph_after(manifest, int(anchor["paragraph_index"]), 4),
            f"Company/logo/legal subject: {company}. Template legal wording requires review. DS_NEED_CONFIRM",
            "fixed_layout.legal_notice",
            preserve_visuals=False,
        )

    template_resume = first_anchor(manifest, "template", "version", "resume")
    if template_resume:
        start = int(template_resume["paragraph_index"])
        paragraph_indexes = sorted(paragraph_infos(manifest))
        if paragraph_indexes:
            end = paragraph_indexes[-1]
            ops["clear_paragraph_ranges"].append({
                "start": start,
                "end": end,
                "source_slot": "cleanup.remove_template_version_resume",
                "preserve_visuals": False,
            })
            ops["remove_visuals_in_ranges"].append({
                "start": start,
                "end": end,
                "source_slot": "cleanup.remove_template_version_resume",
            })
        ops["remove_tables"].extend(tables_after_paragraph(manifest, start))

    for key in ("remove_tables",):
        ops[key] = sorted({int(value) for value in ops[key]})
    ops["metadata"] = {
        "generator": "build_block_ops_from_model.py",
        "product": product,
        "manifest_driven": True,
    }
    return ops


def overlay_explicit_slot_ops(model: dict[str, Any], ops: dict[str, Any]) -> None:
    slot_map = model.get("slot_map")
    if not isinstance(slot_map, list):
        return
    for item in slot_map:
        if not isinstance(item, dict):
            continue
        target = item.get("target")
        if not isinstance(target, dict):
            continue
        source_slot = str(item.get("slot", "slot_map"))
        if "paragraph_index" in target and "text" in item:
            add_paragraph(ops, int(target["paragraph_index"]), str(item["text"]), source_slot)
        if "table_index" in target and isinstance(item.get("rows"), list):
            add_table(ops, int(target["table_index"]), item["rows"], source_slot)
        if "remove_table_index" in target:
            ops["remove_tables"].append(int(target["remove_table_index"]))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build manifest-driven block patch operations from datasheet_model.")
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)

    try:
        model = load_model(args.model)
        manifest = template_manifest(model)
        ops = build_heuristic_ops(model, manifest)
        overlay_explicit_slot_ops(model, ops)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(ops, ensure_ascii=False, indent=2), encoding="utf-8")
        payload = {
            "status": "written",
            "output": str(args.output),
            "paragraphs": len(ops["paragraphs"]),
            "clear_paragraph_ranges": len(ops["clear_paragraph_ranges"]),
            "replace_paragraph_ranges": len(ops["replace_paragraph_ranges"]),
            "remove_visuals_in_ranges": len(ops["remove_visuals_in_ranges"]),
            "tables": len(ops["tables"]),
            "remove_tables": len(ops["remove_tables"]),
            "insert_tables_after_paragraphs": len(ops["insert_tables_after_paragraphs"]),
            "remove_empty_trailing_paragraphs": bool(ops.get("remove_empty_trailing_paragraphs")),
            "manifest_driven": True,
        }
    except Exception as exc:  # noqa: BLE001 - CLI should report compact failures.
        payload = {"status": "failed", "errors": [str(exc)]}
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["status"] == "written" else 1


if __name__ == "__main__":
    raise SystemExit(main())
