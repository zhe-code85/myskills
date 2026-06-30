#! python3
"""Validate ncs-datasheet-gen input gate state before generation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


REQUIRED_GATES = [
    "template_datasheet",
    "competitor_datasheet",
    "historical_product",
    "datasheet_goal",
    "target_product_model",
    "target_package",
    "pin_to_pin_target",
    "allowed_pin_differences",
    "pinout_package_asset_priority",
    "document_status",
    "company_subject",
    "logo_policy",
    "legal_support_subject",
    "competitor_image_policy",
    "output_delivery_preference",
]

COMPLETE_STATUSES = {
    "confirmed",
    "skipped-with-marking",
    "not-used",
    "not-applicable",
    "accepted-with-notes",
}

INCOMPLETE_STATUSES = {
    "",
    "pending",
    "draft",
    "unknown",
    "unconfirmed",
    "need-confirm",
    "needs-confirmation",
}


def normalize_status(value: Any) -> str:
    return str(value or "").strip().lower().replace("_", "-")


def load_gate_rows(path: Path) -> dict[str, dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    raw_gates = data.get("gates", data) if isinstance(data, dict) else data
    rows: dict[str, dict[str, Any]] = {}

    if isinstance(raw_gates, dict):
        for gate_id, value in raw_gates.items():
            if isinstance(value, dict):
                rows[str(gate_id)] = value
            else:
                rows[str(gate_id)] = {"status": value}
        return rows

    if isinstance(raw_gates, list):
        for item in raw_gates:
            if not isinstance(item, dict):
                continue
            gate_id = item.get("id") or item.get("gate") or item.get("name")
            if gate_id:
                rows[str(gate_id)] = item
        return rows

    raise ValueError("input gate JSON must contain a gates object or list")


def validate_gates(
    rows: dict[str, dict[str, Any]],
    *,
    required_gates: list[str],
    allow_blocked: bool,
) -> dict[str, Any]:
    missing: list[str] = []
    pending: list[dict[str, str]] = []
    blocked: list[dict[str, str]] = []
    complete: list[str] = []
    unknown_status: list[dict[str, str]] = []

    for gate_id in required_gates:
        row = rows.get(gate_id)
        if row is None:
            missing.append(gate_id)
            continue
        status = normalize_status(row.get("status"))
        if status in COMPLETE_STATUSES:
            complete.append(gate_id)
        elif status == "blocked":
            if allow_blocked:
                complete.append(gate_id)
            else:
                blocked.append({"id": gate_id, "status": status})
        elif status in INCOMPLETE_STATUSES:
            pending.append({"id": gate_id, "status": status or "pending"})
        else:
            unknown_status.append({"id": gate_id, "status": status})

    errors: list[str] = []
    if missing:
        errors.append("missing required gates: " + ", ".join(missing))
    if pending:
        errors.append("pending gates: " + ", ".join(item["id"] for item in pending))
    if blocked:
        errors.append("blocked gates: " + ", ".join(item["id"] for item in blocked))
    if unknown_status:
        errors.append(
            "unknown gate statuses: "
            + ", ".join(f"{item['id']}={item['status']}" for item in unknown_status)
        )

    return {
        "status": "failed" if errors else "passed",
        "required_gate_count": len(required_gates),
        "complete_gate_count": len(complete),
        "missing": missing,
        "pending": pending,
        "blocked": blocked,
        "unknown_status": unknown_status,
        "errors": errors,
        "warnings": [],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate ncs-datasheet-gen input gate state.")
    parser.add_argument("--gate", type=Path, required=True, help="input-gate.json path")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    parser.add_argument(
        "--required-gate",
        action="append",
        dest="required_gates",
        help="Required gate id. Repeat to override the default 15-gate set.",
    )
    parser.add_argument("--allow-blocked", action="store_true", help="Treat blocked gates as completed audit records.")
    args = parser.parse_args(argv)

    try:
        payload = validate_gates(
            load_gate_rows(args.gate),
            required_gates=args.required_gates or REQUIRED_GATES,
            allow_blocked=args.allow_blocked,
        )
    except Exception as exc:  # noqa: BLE001 - CLI should report compact structural failures.
        payload = {"status": "failed", "errors": [str(exc)], "warnings": []}

    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"status: {payload['status']}")
        for message in payload.get("errors", []):
            print(f"error: {message}")
        for message in payload.get("warnings", []):
            print(f"warning: {message}")

    return 0 if payload["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
