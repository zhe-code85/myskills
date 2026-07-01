#!/usr/bin/env python3
"""Generate editable Draw.io FSM diagrams from a protocol-agnostic FSM JSON file.

The script intentionally understands only generic FSM concepts: states,
transitions, reset entry, confidence, layout hints, routes, and labels. It does
not encode any protocol/IP-specific semantics.
"""

from __future__ import annotations

import argparse
import html
import json
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

STATE_W = 96
STATE_H = 72
PAGE_W = 1400
PAGE_H = 900

STATE_STYLE = "ellipse;whiteSpace=wrap;html=1;fillColor={fill};strokeColor=#000000;strokeWidth=1;fontFamily=Consolas;fontSize=12;fontStyle=1"
TEXT_STYLE = "text;html=1;align=center;verticalAlign=middle;fontFamily=Consolas;fontSize=10;fontColor=#000000;fillColor=none;strokeColor=none;"
TITLE_STYLE = "text;html=1;align=left;verticalAlign=middle;fontFamily=Consolas;fontSize=16;fontStyle=1;fontColor=#000000;fillColor=none;strokeColor=none;"
NOTE_STYLE = "text;html=1;align=left;verticalAlign=top;fontFamily=Consolas;fontSize=10;fontColor=#333333;fillColor=none;strokeColor=none;"
EDGE_STYLE = "edgeStyle=orthogonalEdgeStyle;rounded=1;html=1;strokeColor=#000000;strokeWidth=1;endArrow=classic"
DASHED_EDGE_STYLE = EDGE_STYLE + ";dashed=1"

ALLOWED_LAYOUTS = {"linear", "loop_2row", "error_cleanup", "branched", "custom"}
ALLOWED_MODES = {"strict", "engineering_draft"}
ALLOWED_CONFIDENCE = {"explicit", "derived", "assumed_cleanup"}
ALLOWED_EDGE_STYLE = {"solid", "dashed"}


class FsmError(Exception):
    """Raised for invalid or unsupported FSM input."""


@dataclass
class State:
    name: str
    kind: str = "normal"
    description: str = ""
    x: float | None = None
    y: float | None = None
    w: float = STATE_W
    h: float = STATE_H


@dataclass
class Transition:
    source: str
    target: str
    label: str = ""
    style: str = "solid"
    confidence: str = "explicit"
    source_ref: str = ""
    route: list[tuple[float, float]] = field(default_factory=list)
    label_pos: tuple[float, float, float, float] | None = None


@dataclass
class Fsm:
    title: str
    source: str
    mode: str
    layout: str
    reset_state: str
    states: list[State]
    transitions: list[Transition]
    notes: list[str]
    warnings: list[str] = field(default_factory=list)


def require_string(obj: dict[str, Any], key: str, context: str, default: str | None = None) -> str:
    value = obj.get(key, default)
    if value is None or not isinstance(value, str) or not value.strip():
        raise FsmError(f"{context}: missing or invalid string field {key!r}")
    return value.strip()


def parse_layout(layout_obj: dict[str, Any] | None) -> tuple[float | None, float | None, float, float]:
    if not layout_obj:
        return None, None, STATE_W, STATE_H
    x = layout_obj.get("x")
    y = layout_obj.get("y")
    w = layout_obj.get("w", STATE_W)
    h = layout_obj.get("h", STATE_H)
    for key, value in (("x", x), ("y", y), ("w", w), ("h", h)):
        if value is not None and not isinstance(value, (int, float)):
            raise FsmError(f"state layout field {key!r} must be numeric")
    return x, y, float(w), float(h)


def parse_route(route_obj: dict[str, Any] | None) -> list[tuple[float, float]]:
    if not route_obj:
        return []
    points = route_obj.get("points", [])
    if not isinstance(points, list):
        raise FsmError("transition route.points must be a list")
    parsed: list[tuple[float, float]] = []
    for index, point in enumerate(points):
        if not isinstance(point, dict) or not isinstance(point.get("x"), (int, float)) or not isinstance(point.get("y"), (int, float)):
            raise FsmError(f"transition route.points[{index}] must have numeric x/y")
        parsed.append((float(point["x"]), float(point["y"])))
    return parsed


def parse_label_pos(obj: dict[str, Any] | None) -> tuple[float, float, float, float] | None:
    if not obj:
        return None
    values = []
    for key in ("x", "y", "w", "h"):
        value = obj.get(key)
        if not isinstance(value, (int, float)):
            raise FsmError(f"label_pos.{key} must be numeric")
        values.append(float(value))
    return tuple(values)  # type: ignore[return-value]


def load_fsm(path: Path) -> Fsm:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise FsmError("top-level JSON must be an object")

    title = require_string(data, "title", "fsm", "FSM")
    source = str(data.get("source", "")).strip()
    mode = require_string(data, "mode", "fsm", "engineering_draft")
    layout = require_string(data, "layout", "fsm", "linear")
    reset_state = require_string(data, "reset_state", "fsm")
    notes_raw = data.get("notes", [])
    if not isinstance(notes_raw, list) or not all(isinstance(note, str) for note in notes_raw):
        raise FsmError("notes must be a list of strings")

    if mode not in ALLOWED_MODES:
        raise FsmError(f"mode {mode!r} is not supported; expected one of {sorted(ALLOWED_MODES)}")
    if layout not in ALLOWED_LAYOUTS:
        raise FsmError(f"layout {layout!r} is not supported; expected one of {sorted(ALLOWED_LAYOUTS)}")

    states_raw = data.get("states")
    if not isinstance(states_raw, list) or not states_raw:
        raise FsmError("states must be a non-empty list")
    states: list[State] = []
    seen: set[str] = set()
    for index, raw in enumerate(states_raw):
        if not isinstance(raw, dict):
            raise FsmError(f"states[{index}] must be an object")
        name = require_string(raw, "name", f"states[{index}]")
        if name in seen:
            raise FsmError(f"duplicate state name {name!r}")
        seen.add(name)
        x, y, w, h = parse_layout(raw.get("layout"))
        states.append(
            State(
                name=name,
                kind=str(raw.get("kind", "normal")).strip() or "normal",
                description=str(raw.get("description", "")).strip(),
                x=x,
                y=y,
                w=w,
                h=h,
            )
        )

    if reset_state not in seen:
        raise FsmError(f"reset_state {reset_state!r} does not match any state")

    transitions_raw = data.get("transitions", [])
    if not isinstance(transitions_raw, list):
        raise FsmError("transitions must be a list")
    transitions: list[Transition] = []
    for index, raw in enumerate(transitions_raw):
        if not isinstance(raw, dict):
            raise FsmError(f"transitions[{index}] must be an object")
        source_state = require_string(raw, "from", f"transitions[{index}]")
        target_state = require_string(raw, "to", f"transitions[{index}]")
        if source_state not in seen:
            raise FsmError(f"transitions[{index}].from references unknown state {source_state!r}")
        if target_state not in seen:
            raise FsmError(f"transitions[{index}].to references unknown state {target_state!r}")
        edge_style = str(raw.get("style", "solid")).strip() or "solid"
        confidence = str(raw.get("confidence", "explicit")).strip() or "explicit"
        if edge_style not in ALLOWED_EDGE_STYLE:
            raise FsmError(f"transitions[{index}].style {edge_style!r} is not supported")
        if confidence not in ALLOWED_CONFIDENCE:
            raise FsmError(f"transitions[{index}].confidence {confidence!r} is not supported")
        if mode == "strict" and confidence != "explicit":
            raise FsmError(f"strict mode transition {source_state!r}->{target_state!r} cannot use confidence={confidence!r}")
        transitions.append(
            Transition(
                source=source_state,
                target=target_state,
                label=str(raw.get("label", "")).strip(),
                style=edge_style,
                confidence=confidence,
                source_ref=str(raw.get("source_ref", "")).strip(),
                route=parse_route(raw.get("route")),
                label_pos=parse_label_pos(raw.get("label_pos")),
            )
        )

    fsm = Fsm(title=title, source=source, mode=mode, layout=layout, reset_state=reset_state, states=states, transitions=transitions, notes=list(notes_raw))
    lint_fsm(fsm)
    return fsm


def lint_fsm(fsm: Fsm) -> None:
    if not fsm.transitions:
        fsm.warnings.append("FSM has no transitions; confirm this is intended before rendering.")
    for transition in fsm.transitions:
        if transition.confidence in {"derived", "assumed_cleanup"} and not transition.source_ref:
            fsm.warnings.append(f"{transition.source}->{transition.target} is {transition.confidence} but has no source_ref.")
        if transition.confidence == "assumed_cleanup" and transition.style != "dashed":
            fsm.warnings.append(f"{transition.source}->{transition.target} is assumed_cleanup but style is not dashed.")
    if fsm.layout == "loop_2row" and not any(t.source != t.target for t in fsm.transitions):
        fsm.warnings.append("layout loop_2row selected but no non-self transition was found.")
    if len(fsm.states) > 15 and fsm.layout != "custom":
        fsm.warnings.append("FSM has more than 15 states; consider custom layout or overview/detail pages.")


def assign_layout(fsm: Fsm) -> None:
    states_without_xy = [state for state in fsm.states if state.x is None or state.y is None]
    if not states_without_xy:
        return
    if fsm.layout == "custom":
        raise FsmError("custom layout requires every state to provide layout.x and layout.y")

    # Preserve input order; templates are structural, not protocol-specific.
    n = len(fsm.states)
    if fsm.layout == "linear":
        start_x, y, gap = 100, 240, 150
        for i, state in enumerate(fsm.states):
            if state.x is None:
                state.x = start_x + i * gap
            if state.y is None:
                state.y = y
        return

    if fsm.layout in {"loop_2row", "error_cleanup"}:
        top_count = min(max((n + 1) // 2, 1), 7)
        start_x, top_y, bottom_y, gap = 100, 190, 430, 150
        for i, state in enumerate(fsm.states):
            if state.x is not None and state.y is not None:
                continue
            if i < top_count:
                state.x = start_x + i * gap if state.x is None else state.x
                state.y = top_y if state.y is None else state.y
            else:
                j = i - top_count
                state.x = start_x + (top_count - 1 - j) * gap if state.x is None else state.x
                state.y = bottom_y if state.y is None else state.y
        return

    if fsm.layout == "branched":
        center_x, center_y = 640, 260
        radius_x, radius_y = 240, 160
        for i, state in enumerate(fsm.states):
            if state.x is not None and state.y is not None:
                continue
            if i == 0:
                state.x = 120 if state.x is None else state.x
                state.y = center_y if state.y is None else state.y
            else:
                row = (i - 1) // 3
                col = (i - 1) % 3
                state.x = center_x + (col - 1) * radius_x if state.x is None else state.x
                state.y = center_y + (row - 0.5) * radius_y if state.y is None else state.y
        return


def fill_for_kind(kind: str) -> str:
    lowered = kind.lower()
    if lowered in {"idle", "done", "complete", "terminal"}:
        return "#D9EAD3"
    if lowered in {"error", "fault", "abort", "timeout"}:
        return "#FCE5CD"
    if lowered in {"cleanup", "recover", "recovery"}:
        return "#FFF2CC"
    return "#FFFFFF"


def add_cell(root: ET.Element, cell_id: int, value: str = "", style: str | None = None, vertex: bool = False, edge: bool = False, parent: str = "1", source: str | None = None, target: str | None = None) -> ET.Element:
    attrs = {"id": str(cell_id)}
    if value:
        attrs["value"] = value
    elif edge:
        attrs["value"] = ""
    if style is not None:
        attrs["style"] = style
    if vertex:
        attrs["vertex"] = "1"
    if edge:
        attrs["edge"] = "1"
    attrs["parent"] = parent
    if source is not None:
        attrs["source"] = source
    if target is not None:
        attrs["target"] = target
    return ET.SubElement(root, "mxCell", attrs)


def add_geometry(cell: ET.Element, x: float | None = None, y: float | None = None, w: float | None = None, h: float | None = None, relative: bool = False, points: list[tuple[float, float]] | None = None, source_point: tuple[float, float] | None = None, target_point: tuple[float, float] | None = None) -> None:
    attrs: dict[str, str] = {"as": "geometry"}
    if relative:
        attrs["relative"] = "1"
    if x is not None:
        attrs["x"] = f"{x:g}"
    if y is not None:
        attrs["y"] = f"{y:g}"
    if w is not None:
        attrs["width"] = f"{w:g}"
    if h is not None:
        attrs["height"] = f"{h:g}"
    geom = ET.SubElement(cell, "mxGeometry", attrs)
    if points:
        arr = ET.SubElement(geom, "Array", {"as": "points"})
        for px, py in points:
            ET.SubElement(arr, "mxPoint", {"x": f"{px:g}", "y": f"{py:g}"})
    if source_point:
        ET.SubElement(geom, "mxPoint", {"x": f"{source_point[0]:g}", "y": f"{source_point[1]:g}", "as": "sourcePoint"})
    if target_point:
        ET.SubElement(geom, "mxPoint", {"x": f"{target_point[0]:g}", "y": f"{target_point[1]:g}", "as": "targetPoint"})


def default_label_pos(src: State, dst: State, index: int) -> tuple[float, float, float, float]:
    sx = (src.x or 0) + src.w / 2
    sy = (src.y or 0) + src.h / 2
    tx = (dst.x or 0) + dst.w / 2
    ty = (dst.y or 0) + dst.h / 2
    x = (sx + tx) / 2 - 65
    y = (sy + ty) / 2 - 38
    if abs(sy - ty) < 20:
        y -= 28 if index % 2 == 0 else -34
    return x, y, 130, 32


def generate_drawio(fsm: Fsm) -> str:
    assign_layout(fsm)
    mxfile = ET.Element("mxfile", {"host": "app.diagrams.net"})
    diagram = ET.SubElement(mxfile, "diagram", {"name": safe_name(fsm.title), "id": "1"})
    model = ET.SubElement(
        diagram,
        "mxGraphModel",
        {
            "dx": "1400",
            "dy": "900",
            "grid": "1",
            "gridSize": "10",
            "guides": "1",
            "tooltips": "1",
            "connect": "1",
            "arrows": "1",
            "fold": "1",
            "page": "1",
            "pageScale": "1",
            "pageWidth": str(PAGE_W),
            "pageHeight": str(PAGE_H),
            "background": "#FFFFFF",
        },
    )
    root = ET.SubElement(model, "root")
    ET.SubElement(root, "mxCell", {"id": "0"})
    ET.SubElement(root, "mxCell", {"id": "1", "parent": "0"})

    next_id = 2
    title_cell = add_cell(root, next_id, html.escape(fsm.title), TITLE_STYLE, vertex=True)
    add_geometry(title_cell, 60, 30, 520, 34)
    next_id += 1
    if fsm.source:
        src_cell = add_cell(root, next_id, html.escape(f"Source: {fsm.source}"), NOTE_STYLE, vertex=True)
        add_geometry(src_cell, 60, 66, 620, 24)
        next_id += 1

    state_ids: dict[str, int] = {}
    for state in fsm.states:
        state_ids[state.name] = next_id
        value = state.name if not state.description else f"{state.name}&#xa;{html.escape(state.description)}"
        cell = add_cell(root, next_id, value, STATE_STYLE.format(fill=fill_for_kind(state.kind)), vertex=True)
        add_geometry(cell, state.x, state.y, state.w, state.h)
        next_id += 1

    # Reset entry arrow.
    reset = next((s for s in fsm.states if s.name == fsm.reset_state), None)
    if reset is not None:
        edge = add_cell(root, next_id, "", EDGE_STYLE, edge=True, target=str(state_ids[reset.name]))
        add_geometry(edge, relative=True, source_point=((reset.x or 0) - 45, (reset.y or 0) + reset.h / 2))
        next_id += 1
        label = add_cell(root, next_id, "reset", TEXT_STYLE, vertex=True)
        add_geometry(label, (reset.x or 0) - 70, (reset.y or 0) + reset.h / 2 - 28, 58, 20)
        next_id += 1

    state_by_name = {state.name: state for state in fsm.states}
    for index, transition in enumerate(fsm.transitions):
        src = state_by_name[transition.source]
        dst = state_by_name[transition.target]
        style = DASHED_EDGE_STYLE if transition.style == "dashed" else EDGE_STYLE
        edge = add_cell(root, next_id, "", style, edge=True, source=str(state_ids[src.name]), target=str(state_ids[dst.name]))
        add_geometry(edge, relative=True, points=transition.route)
        next_id += 1
        if transition.label:
            x, y, w, h = transition.label_pos or default_label_pos(src, dst, index)
            label = add_cell(root, next_id, html.escape(transition.label).replace("\n", "&#xa;"), TEXT_STYLE, vertex=True)
            add_geometry(label, x, y, w, h)
            next_id += 1

    legend_lines: list[str] = []
    if any(t.confidence == "assumed_cleanup" for t in fsm.transitions):
        legend_lines.append("dashed = assumed cleanup/recovery")
    if any(t.confidence == "derived" for t in fsm.transitions):
        legend_lines.append("derived = from design prose")
    legend_lines.extend(fsm.notes)
    if legend_lines:
        note = add_cell(root, next_id, html.escape("Notes:\n" + "\n".join(f"- {line}" for line in legend_lines)).replace("\n", "&#xa;"), NOTE_STYLE, vertex=True)
        add_geometry(note, 60, PAGE_H - 150, 520, 110)

    indent_xml(mxfile)
    return ET.tostring(mxfile, encoding="unicode")


def safe_name(value: str) -> str:
    return "".join(ch if ch.isalnum() or ch in "-_ " else "-" for ch in value).strip()[:80] or "fsm"


def indent_xml(elem: ET.Element, level: int = 0) -> None:
    i = "\n" + level * "  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        for child in elem:
            indent_xml(child, level + 1)
        if not child.tail or not child.tail.strip():  # type: ignore[possibly-undefined]
            child.tail = i  # type: ignore[possibly-undefined]
    if level and (not elem.tail or not elem.tail.strip()):
        elem.tail = i


def write_trace(fsm: Fsm, path: Path) -> None:
    lines = ["| 迁移 | 标签 | 来源 | 类型 |", "| --- | --- | --- | --- |"]
    for t in fsm.transitions:
        label = t.label.replace("|", "\\|")
        src = t.source_ref or "未标注"
        lines.append(f"| `{t.source} -> {t.target}` | `{label}` | {src} | `{t.confidence}` |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="FSM JSON input path")
    parser.add_argument("--output", help="Draw.io output path")
    parser.add_argument("--emit-trace", help="Write a markdown transition traceability table")
    parser.add_argument("--lint", action="store_true", help="Only validate/lint the FSM JSON")
    parser.add_argument("--fail-on-warning", action="store_true", help="Return non-zero when warnings are produced")
    args = parser.parse_args(argv)

    try:
        fsm = load_fsm(Path(args.input))
        if fsm.warnings:
            print("WARNINGS:", file=sys.stderr)
            for warning in fsm.warnings:
                print(f"- {warning}", file=sys.stderr)
            if args.fail_on_warning:
                return 2
        if args.lint:
            print(f"OK: {len(fsm.states)} state(s), {len(fsm.transitions)} transition(s)")
            return 0
        if not args.output:
            raise FsmError("--output is required unless --lint is used")
        xml = generate_drawio(fsm)
        Path(args.output).write_text(xml, encoding="utf-8")
        if args.emit_trace:
            write_trace(fsm, Path(args.emit_trace))
        print(f"OK: wrote {args.output}")
        print(f"States: {len(fsm.states)}")
        print(f"Transitions: {len(fsm.transitions)}")
        if args.emit_trace:
            print(f"Trace: {args.emit_trace}")
        return 0
    except (OSError, json.JSONDecodeError, FsmError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
