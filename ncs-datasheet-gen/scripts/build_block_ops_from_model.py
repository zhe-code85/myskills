#! python3
"""Build conservative paragraph/table block operations from a normalized datasheet_model."""

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


def blank_range(start: int, end: int) -> list[dict[str, Any]]:
    return [{"index": index, "text": ""} for index in range(start, end + 1)]


def para(index: int, text: str) -> dict[str, Any]:
    return {"index": index, "text": text}


def table(index: int, rows: list[list[Any]]) -> dict[str, Any]:
    return {"index": index, "rows": rows}


def compact(text: str, limit: int = 170) -> str:
    text = re.sub(r"\s+", " ", str(text)).strip()
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


def value_text(item: dict[str, Any]) -> str:
    parts = []
    for key in ("min", "typ", "max", "value"):
        value = item.get(key)
        if value not in (None, ""):
            parts.append(f"{key.upper()}={value}")
    if not parts:
        parts.append("DS_TBD")
    unit = item.get("unit", "")
    return " / ".join(parts) + (f" {unit}" if unit else "")


def build_paragraphs(model: dict[str, Any]) -> list[dict[str, Any]]:
    md = model["metadata"]
    semi = model["semi_structured_sections"]
    paragraphs: list[dict[str, Any]] = [
        para(0, "DESCRIPTION"),
        para(1, compact(semi["description"][0], 230)),
        para(2, compact(semi["description"][1], 230)),
        para(3, compact(semi["description"][2], 230)),
        para(4, "Company/logo/legal subject: NCS. Template legal wording requires review. DS_NEED_CONFIRM"),
        para(5, "FEATURES"),
        para(23, "APPLICATIONS"),
        para(28, "TYPICAL APPLICATION"),
        para(29, "DS_PLACEHOLDER_IMAGE: Typical application diagram to be redrawn from NCS-owned artwork. DS_COMPETITOR_REF DS_NEED_CONFIRM"),
        para(51, "ORDER INFORMATION"),
        para(52, "Notes: Device suffix, top marking, lead finish, MSL, and MOQ require ERP/QA/package-team confirmation. DS_NEED_CONFIRM"),
        para(54, ""),
        para(55, ""),
        para(57, ""),
        para(58, ""),
        para(60, "DEVICE INFORMATION"),
        para(62, "PIN CONFIGURATION"),
        para(63, "TOP VIEW"),
        para(65, "PIN DESCRIPTION"),
        para(67, ""),
        para(68, ""),
        para(70, ""),
        para(71, "Note:"),
        para(72, "P = power, I = input, O = output, G = ground. Pin map is a competitor-derived pin-to-pin target. DS_COMPETITOR_REF DS_NEED_CONFIRM"),
        para(76, "ABSOLUTE MAXIMUM RATING"),
        para(87, "RECOMMENDED OPERATING CONDITIONS"),
        para(91, "THERMAL PERFORMANCE"),
        para(92, "Notes:"),
        para(93, "Thermal data for NCS25D31B 16-pin VQFN is not confirmed. Package-team simulation or measurement is required before clean release. DS_TBD DS_NEED_CONFIRM"),
        para(108, "ELECTRICAL CHARACTERISTICS"),
        para(111, "Notes:"),
        para(112, "Unless otherwise stated, target values are from LMK1D2102 and are not NCS production-guaranteed specifications. DS_COMPETITOR_REF DS_UNVERIFIED_SPEC DS_NEED_CONFIRM"),
        para(115, "BLOCK DIAGRAM"),
        para(116, "DS_PLACEHOLDER_IMAGE: Functional block diagram target requires NCS-owned redraw before clean release."),
        para(118, "TYPICAL PERFORMANCE CHARACTERISTICS"),
        para(120, "DS_PLACEHOLDER_IMAGE: Typical curves from competitor are target references only. NCS characterization is required."),
        para(122, "FUNCTIONAL DESCRIPTION"),
        para(123, compact(semi["functional_description"][0], 240)),
        para(124, "Input Interface"),
        para(125, "The target input stage accepts differential or single-ended clock sources and supports AC- or DC-coupled configurations. DS_COMPETITOR_REF DS_NEED_CONFIRM"),
        para(126, "LVDS Output Termination"),
        para(127, compact(semi["functional_description"][1], 240)),
        para(128, "Output Control and Fail-Safe Operation"),
        para(129, compact(semi["functional_description"][2], 240)),
        para(139, "Historical Product Boundary"),
        para(140, "NCS25D31 history supports a larger 48-pin, 10-output multi-standard buffer. It is useful as NCS clock-buffer baseline, but does not establish NCS25D31B pinout/package/final limits. DS_MISSING_HISTORY"),
        para(199, "APPLICATION INFORMATION"),
        para(200, "Application Information"),
        para(201, compact(semi["application_information"][0], 220)),
        para(203, compact(semi["application_information"][1], 220)),
        para(204, compact(semi["application_information"][2], 220)),
        para(209, "Power Supply Recommendations"),
        para(210, compact(semi["power_supply_recommendations"][0], 220)),
        para(211, compact(semi["power_supply_recommendations"][1], 220)),
        para(222, "PCB Layout Note"),
        para(223, compact(semi["layout_guidelines"][0], 220)),
        para(224, compact(semi["layout_guidelines"][1], 220)),
        para(225, compact(semi["layout_guidelines"][2], 220)),
    ]

    features = semi["features"]
    for offset, feature in enumerate(features[:15]):
        paragraphs.append(para(6 + offset, "- " + compact(feature, 150)))
    paragraphs.extend(blank_range(6 + min(len(features), 15), 22))

    apps = semi["applications"]
    for offset, app in enumerate(apps[:4]):
        paragraphs.append(para(24 + offset, "- " + compact(app, 120)))

    ratings = model["structured_sections"]["absolute_maximum_ratings"]
    for offset, item in enumerate(ratings[:8]):
        paragraphs.append(para(77 + offset, f"{item['parameter']} ................................ {value_text(item)}"))
    paragraphs.append(para(85, "ESD ratings are target references and require NCS qualification. DS_COMPETITOR_REF DS_UNVERIFIED_SPEC DS_NEED_CONFIRM"))
    paragraphs.append(para(86, ""))

    roc = model["structured_sections"]["recommended_operating_conditions"]
    for offset, item in enumerate(roc[:4]):
        paragraphs.append(para(88 + offset, f"{item['parameter']} ................................ {value_text(item)}"))

    # Clear old power-management prose after the LVDS functional-description replacement.
    paragraphs.extend(blank_range(130, 138))
    paragraphs.extend(blank_range(141, 198))
    paragraphs.extend(blank_range(205, 208))
    paragraphs.extend(blank_range(212, 221))

    return paragraphs


def build_tables(model: dict[str, Any]) -> list[dict[str, Any]]:
    ss = model["structured_sections"]
    order = ss["ordering"][0]
    dev = ss["device_information"][0]

    pin_rows = [["Pin", "Name", "Type", "Description"]]
    for pin in ss["pins"]:
        pin_rows.append([pin["pin_number"], pin["pin_name"], pin["pin_type"], compact(pin["function"], 95)])

    thermal_rows = [
        ["Thermal Metric", "Description", "NCS25D31B 16-pin VQFN", "Status", "Unit"],
        ["thetaJA", "Junction-to-ambient thermal resistance", "DS_TBD", "DS_NEED_CONFIRM", "degC/W"],
        ["thetaJC(top)", "Junction-to-case top thermal resistance", "DS_TBD", "DS_NEED_CONFIRM", "degC/W"],
        ["thetaJB", "Junction-to-board thermal resistance", "DS_TBD", "DS_NEED_CONFIRM", "degC/W"],
        ["psiJT", "Junction-to-top characterization parameter", "DS_TBD", "DS_NEED_CONFIRM", "degC/W"],
        ["psiJB", "Junction-to-board characterization parameter", "DS_TBD", "DS_NEED_CONFIRM", "degC/W"],
        ["thetaJC(bot)", "Junction-to-case bottom thermal resistance", "DS_TBD", "DS_NEED_CONFIRM", "degC/W"],
    ]

    ec_rows = [["Item", "Symbol/Name", "Condition", "Min", "Typ", "Max", "Unit", "Status"]]
    for section in ("electrical_characteristics", "timing_characteristics"):
        for item in ss[section]:
            ec_rows.append([
                compact(item.get("parameter", item.get("name", "")), 45),
                compact(item.get("name", ""), 24),
                compact(item.get("test_condition", ""), 72),
                item.get("min", ""),
                item.get("typ", item.get("value", "")),
                item.get("max", ""),
                item.get("unit", ""),
                item.get("status", "DS_COMPETITOR_REF; DS_UNVERIFIED_SPEC; DS_NEED_CONFIRM"),
            ])

    return [
        table(0, [
            ["DEVICE", "PACKAGE", "TOP MARKING", "ENVIRONMENTAL", "SHIPPING METHOD", "MOQ"],
            [order["device"], order["package"], order["top_marking"], order["environmental"], order["shipping_method"], order["moq"]],
            ["Notes", "All order information requires confirmation.", "DS_NEED_CONFIRM", "", "", ""],
        ]),
        table(3, [
            ["DEVICE", "OPERATION MODE", "PACKAGE", "MSL", "STATUS"],
            [dev["device"], dev["operation_mode"], dev["package"], dev["msl"], dev["status"]],
            ["Source/status", dev["source"], dev["marking"], "", ""],
        ]),
        table(5, pin_rows),
        table(6, thermal_rows),
        table(7, ec_rows),
        table(8, [
            ["Typical Characteristic / Figure", "Status"],
            ["Current consumption vs frequency and VDD target", "DS_PLACEHOLDER_IMAGE DS_COMPETITOR_REF"],
            ["VOD vs frequency target", "DS_PLACEHOLDER_IMAGE DS_COMPETITOR_REF"],
            ["Output phase noise target", "DS_PLACEHOLDER_IMAGE DS_COMPETITOR_REF"],
            ["NCS measured curves", "DS_TBD DS_NEED_CONFIRM"],
        ]),
        table(9, [
            ["Typical Performance Figure", "Status"],
            ["Supply current, output phase noise, additive jitter, skew, and PSNR curves", "DS_PLACEHOLDER_IMAGE DS_COMPETITOR_REF DS_NEED_CONFIRM"],
            ["NCS measured characterization curves", "DS_TBD DS_NEED_CONFIRM"],
        ]),
        table(10, [
            ["Application / Termination Item", "Target / Note", "Status"],
            ["Differential termination", "100 ohm at receiver", "DS_COMPETITOR_REF"],
            ["AC coupling and reference bias", "Follow receiver common-mode requirements", "DS_COMPETITOR_REF DS_NEED_CONFIRM"],
        ]),
        table(11, [
            ["Layout / Figure Placeholder", "Status"],
            ["PCB layout recommendation and routing examples require NCS-owned drawing", "DS_PLACEHOLDER_IMAGE DS_NEED_CONFIRM"],
        ]),
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description="Build conservative block patch operations from datasheet_model.")
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    model = load_model(args.model)
    ops = {
        "paragraphs": build_paragraphs(model),
        "tables": build_tables(model),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(ops, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"status": "written", "output": str(args.output), "paragraphs": len(ops["paragraphs"]), "tables": len(ops["tables"])}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
