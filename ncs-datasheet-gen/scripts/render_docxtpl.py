#! python3
"""Render a datasheet DOCX from a docxtpl template and datasheet_model."""

from __future__ import annotations

import argparse
import importlib.util
import json
import platform
import sys
from pathlib import Path
from typing import Any


def package_available(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def environment_payload() -> dict[str, Any]:
    return {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "packages": {
            "docxtpl": package_available("docxtpl"),
            "jinja2": package_available("jinja2"),
            "yaml": package_available("yaml"),
            "docx": package_available("docx"),
        },
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
    model = data.get("datasheet_model", data)
    if not isinstance(model, dict):
        raise ValueError("datasheet_model must be a mapping")
    context = dict(data)
    context["datasheet_model"] = model
    for key in ("metadata", "fixed_layout", "semi_structured_sections", "structured_sections", "assets", "markings"):
        context[key] = model.get(key, {})
    return context


def render_docx(template: Path, model_path: Path, output: Path, strict: bool) -> dict[str, Any]:
    if not package_available("docxtpl"):
        raise SystemExit("docxtpl is not installed. Install dependencies from scripts/requirements.txt.")

    from docxtpl import DocxTemplate  # type: ignore

    context = load_model(model_path)
    doc = DocxTemplate(str(template))
    if strict:
        from jinja2 import Environment, StrictUndefined

        env = Environment(undefined=StrictUndefined)
        doc.render(context, jinja_env=env)
    else:
        doc.render(context)
    output.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(output))
    return {
        "status": "rendered",
        "template": str(template),
        "model": str(model_path),
        "output": str(output),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Render a DOCX datasheet with docxtpl and datasheet_model.")
    parser.add_argument("--check-env", action="store_true", help="Print Python/package availability as JSON and exit")
    parser.add_argument("--template", type=Path, help="Path to docxtpl-enabled DOCX template")
    parser.add_argument("--model", type=Path, help="Path to datasheet_model JSON/YAML")
    parser.add_argument("--output", type=Path, help="Output DOCX path")
    parser.add_argument("--strict", action="store_true", help="Fail on undefined template variables")
    parser.add_argument("--report", type=Path, help="Optional JSON render report path")
    args = parser.parse_args(argv)

    if args.check_env:
        print(json.dumps(environment_payload(), ensure_ascii=False, indent=2))
        return 0

    missing = [name for name in ("template", "model", "output") if getattr(args, name) is None]
    if missing:
        parser.error("missing required arguments for rendering: " + ", ".join(f"--{name}" for name in missing))

    try:
        payload = render_docx(args.template, args.model, args.output, args.strict)
    except Exception as exc:  # noqa: BLE001 - CLI should surface render failures cleanly.
        print(json.dumps({"status": "failed", "error": str(exc)}, ensure_ascii=False, indent=2), file=sys.stderr)
        return 1

    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
