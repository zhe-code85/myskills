#!/usr/bin/env python3
"""Convert a small WaveJSON subset into editable Draw.io XML.

The output uses diagrams.net's standard compressed diagram payload so it opens
reliably in the Draw.io client.
"""

from __future__ import annotations

import argparse
import base64
import html
import json
from pathlib import Path
from typing import Iterable, Sequence
from urllib.parse import quote
import zlib
import xml.etree.ElementTree as ET

CW = 40
CH = 40
PAD = 10
LW = 90
X0 = 100
Y0 = 60

BUS_SYMBOLS = {"=", "2", "3", "4", "5"}
LOW_SYMBOLS = {"0", "l"}
HIGH_SYMBOLS = {"1", "h"}
UNKNOWN_SYMBOLS = {"x", "u"}

FILL_BY_BUS_SYMBOL = {
    "=": "none",
    "2": "#F3E5F5",
    "3": "#E8F5E9",
    "4": "#E3F2FD",
    "5": "#FFF3E0",
}

STYLE_WAVE = (
    "endArrow=none;html=1;strokeColor=#333333;strokeWidth=2;rounded=0;"
)
STYLE_GRID = (
    "endArrow=none;html=1;dashed=1;strokeColor=#DDDDDD;"
    "strokeWidth=1;rounded=0;"
)
STYLE_BOUNDARY = (
    "endArrow=none;html=1;dashed=1;strokeColor=#999999;"
    "strokeWidth=2;rounded=0;"
)
STYLE_X = (
    "endArrow=none;html=1;strokeColor=#888888;strokeWidth=1;rounded=0;"
)
STYLE_X_BUS = (
    "endArrow=none;html=1;strokeColor=#A6A6A6;strokeWidth=2;rounded=0;"
)
STYLE_Z = "endArrow=none;html=1;strokeColor=#777777;strokeWidth=2;rounded=0;"
STYLE_BUS_LABEL = (
    "text;html=1;align=center;verticalAlign=middle;fontSize=12;"
    "fontColor=#333333;fillColor=none;strokeColor=none;"
)
STYLE_NAME = (
    "text;html=1;align=right;verticalAlign=middle;fontSize=13;"
    "fontStyle=1;fontColor=#333333;fillColor=none;strokeColor=none;"
)
STYLE_TITLE = (
    "text;html=1;align=center;fontSize=12;fontColor=#666666;"
    "fontStyle=2;fillColor=none;strokeColor=none;"
)


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def cell_vertex(
    cell_id: str,
    value: str,
    style: str,
    x: float,
    y: float,
    w: float,
    h: float,
) -> str:
    return (
        f'        <mxCell id="{esc(cell_id)}" value="{esc(value)}" '
        f'style="{esc(style)}" vertex="1" parent="1">\n'
        f'          <mxGeometry x="{x:g}" y="{y:g}" width="{w:g}" '
        f'height="{h:g}" as="geometry"/>\n'
        f"        </mxCell>"
    )


def cell_edge_points(
    cell_id: str,
    points: list[tuple[float, float]],
    style: str,
) -> str:
    if len(points) < 2:
        raise ValueError(f"edge {cell_id} needs at least two points")
    source = points[0]
    target = points[-1]
    middle = points[1:-1]
    if middle:
        array = "\n".join(
            f'              <mxPoint x="{x:g}" y="{y:g}"/>'
            for x, y in middle
        )
        points_xml = (
            f'\n            <Array as="points">\n{array}\n            </Array>'
        )
    else:
        points_xml = ""
    return (
        f'        <mxCell id="{esc(cell_id)}" value="" '
        f'style="{esc(style)}" edge="1" parent="1">\n'
        f'          <mxGeometry relative="1" as="geometry">\n'
        f'            <mxPoint x="{source[0]:g}" y="{source[1]:g}" '
        f'as="sourcePoint"/>\n'
        f'            <mxPoint x="{target[0]:g}" y="{target[1]:g}" '
        f'as="targetPoint"/>{points_xml}\n'
        f"          </mxGeometry>\n"
        f"        </mxCell>"
    )


def y_levels(row_index: int) -> tuple[float, float, float, float]:
    top = Y0 + row_index * (CH + PAD)
    high = top + 8
    low = top + CH - 8
    mid = (high + low) / 2
    return top, high, low, mid


def normalized_states(wave: str) -> list[str]:
    states: list[str] = []
    prev = "d"
    for char in wave:
        state = prev if char == "." else char
        states.append(state)
        if char != "|":
            prev = state
    return states


def level_y(state: str, high: float, low: float, mid: float) -> float:
    if state in HIGH_SYMBOLS:
        return high
    if state in LOW_SYMBOLS:
        return low
    return mid


def render_clock(
    cell_prefix: str,
    row_index: int,
    wave: str,
    inverted: bool,
) -> list[str]:
    _, high, low, _ = y_levels(row_index)
    if inverted:
        high, low = low, high
    points: list[tuple[float, float]] = []
    beat = 0
    for char in wave:
        if char == "|":
            beat += 1
            continue
        x = X0 + beat * CW
        if not points:
            points.append((x, low))
        points.extend(
            [
                (x, high),
                (x + CW / 2, high),
                (x + CW / 2, low),
                (x + CW, low),
            ]
        )
        beat += 1
    return [
        cell_edge_points(
            f"{cell_prefix}_wave",
            points,
            STYLE_WAVE,
        )
    ]


def render_level(cell_prefix: str, row_index: int, wave: str) -> list[str]:
    _, high, low, mid = y_levels(row_index)
    states = normalized_states(wave)
    points: list[tuple[float, float]] = []
    for i, state in enumerate(states):
        if state == "|":
            continue
        x0 = X0 + i * CW
        x1 = x0 + CW
        y = level_y(state, high, low, mid)
        if not points:
            points.append((x0, y))
        elif points[-1][1] != y:
            points.append((x0, points[-1][1]))
            points.append((x0, y))
        points.append((x1, y))
    return [
        cell_edge_points(
            f"{cell_prefix}_wave",
            points,
            STYLE_WAVE,
        )
    ]


def run_segments(wave: str, symbols: Iterable[str]) -> list[tuple[int, int, str]]:
    wanted = set(symbols)
    states = normalized_states(wave)
    segments: list[tuple[int, int, str]] = []
    start: int | None = None
    current = ""
    for i, state in enumerate(states + ["\0"]):
        if state in wanted:
            if start is None:
                start = i
                current = state
            elif state != current:
                segments.append((start, i, current))
                start = i
                current = state
        elif start is not None:
            segments.append((start, i, current))
            start = None
    return segments


def render_bus(
    cell_prefix: str,
    row_index: int,
    wave: str,
    data: Sequence[object],
) -> list[str]:
    _, high, low, mid = y_levels(row_index)
    cells: list[str] = []
    data_index = 0
    for seg_index, (start, end, symbol) in enumerate(
        run_segments(wave, BUS_SYMBOLS)
    ):
        x0 = X0 + start * CW
        x1 = X0 + end * CW
        fill = FILL_BY_BUS_SYMBOL.get(symbol, "none")
        if fill != "none":
            cells.append(
                cell_vertex(
                    f"{cell_prefix}_bus_bg_{seg_index}",
                    "",
                    f"rounded=0;html=1;fillColor={fill};strokeColor=none;",
                    x0,
                    high - 2,
                    x1 - x0,
                    low - high + 4,
                )
            )
        cells.append(
            cell_edge_points(
                f"{cell_prefix}_bus_top_{seg_index}",
                [(x0, high), (x1, high)],
                STYLE_WAVE,
            )
        )
        cells.append(
            cell_edge_points(
                f"{cell_prefix}_bus_bottom_{seg_index}",
                [(x0, low), (x1, low)],
                STYLE_WAVE,
            )
        )
        label = data[data_index] if data_index < len(data) else symbol
        data_index += 1
        cells.append(
            cell_vertex(
                f"{cell_prefix}_bus_label_{seg_index}",
                str(label),
                STYLE_BUS_LABEL,
                x0,
                mid - 8,
                x1 - x0,
                16,
            )
        )
    for seg_index, (start, end, _) in enumerate(
        run_segments(wave, UNKNOWN_SYMBOLS)
    ):
        x0 = X0 + start * CW
        x1 = X0 + end * CW
        cells.append(
            cell_edge_points(
                f"{cell_prefix}_x_top_{seg_index}",
                [(x0, high), (x1, high)],
                STYLE_X_BUS,
            )
        )
        cells.append(
            cell_edge_points(
                f"{cell_prefix}_x_bottom_{seg_index}",
                [(x0, low), (x1, low)],
                STYLE_X_BUS,
            )
        )

        states = normalized_states(wave)
        left_is_data = start > 0 and states[start - 1] in BUS_SYMBOLS
        right_is_data = end < len(states) and states[end] in BUS_SYMBOLS
        x_marks = []
        if left_is_data:
            x_marks.append(x0)
        if right_is_data:
            x_marks.append(x1)
        if not x_marks:
            x_marks.append((x0 + x1) / 2)

        half = 5
        for mark_index, mark_x in enumerate(x_marks):
            cells.append(
                cell_edge_points(
                    f"{cell_prefix}_x_a_{seg_index}_{mark_index}",
                    [(mark_x - half, mid - half), (mark_x + half, mid + half)],
                    STYLE_X,
                )
            )
            cells.append(
                cell_edge_points(
                    f"{cell_prefix}_x_b_{seg_index}_{mark_index}",
                    [(mark_x - half, mid + half), (mark_x + half, mid - half)],
                    STYLE_X,
                )
            )
    for seg_index, (start, end, _) in enumerate(run_segments(wave, {"z"})):
        x0 = X0 + start * CW
        x1 = X0 + end * CW
        cells.append(
            cell_edge_points(
                f"{cell_prefix}_z_{seg_index}",
                [(x0, mid), (x1, mid)],
                STYLE_Z,
            )
        )
        cells.append(
            cell_vertex(
                f"{cell_prefix}_z_label_{seg_index}",
                "Z",
                (
                    "text;html=1;align=center;verticalAlign=middle;"
                    "fontSize=12;fontColor=#777777;fillColor=none;"
                    "strokeColor=none;"
                ),
                x0,
                mid - 8,
                x1 - x0,
                16,
            )
        )
    if not cells:
        return render_level(cell_prefix, row_index, wave)
    return cells


def normalize_data(value) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return value.split()
    if isinstance(value, list):
        return [str(item) for item in value]
    return [str(value)]


def unsupported_features(payload: dict) -> list[str]:
    issues: list[str] = []
    for key in ("edge", "head", "foot", "config"):
        if key in payload:
            issues.append(f"top-level {key!r}")
    signals = payload.get("signal", [])
    if not isinstance(signals, list):
        issues.append("top-level 'signal' is not a list")
        return issues
    for index, signal in enumerate(signals):
        if isinstance(signal, list):
            issues.append(f"grouped signal at signal[{index}]")
            continue
        if not isinstance(signal, dict):
            issues.append(f"non-object signal at signal[{index}]")
            continue
        wave = str(signal.get("wave", ""))
        if not wave:
            issues.append(f"signal[{index}] missing non-empty wave")
        for key in ("node", "period", "phase"):
            if key in signal:
                issues.append(f"signal[{index}] {key!r}")
    return issues


def render_signal(signal: dict, row_index: int) -> list[str]:
    name = str(signal.get("name", f"sig{row_index}"))
    wave = str(signal.get("wave", ""))
    data = normalize_data(signal.get("data"))
    prefix = f"sig_{row_index}"
    top, _, _, _ = y_levels(row_index)
    cells = [
        cell_vertex(
            f"{prefix}_name",
            name,
            STYLE_NAME,
            10,
            top,
            LW - 10,
            CH,
        )
    ]
    if "p" in wave or "P" in wave:
        cells.extend(render_clock(prefix, row_index, wave, inverted=False))
    elif "n" in wave or "N" in wave:
        cells.extend(render_clock(prefix, row_index, wave, inverted=True))
    elif any(char in wave for char in BUS_SYMBOLS | UNKNOWN_SYMBOLS | {"z"}):
        cells.extend(render_bus(prefix, row_index, wave, data))
    else:
        cells.extend(render_level(prefix, row_index, wave))
    return cells


def render_boundaries(signals: list[dict], beats: int) -> list[str]:
    height = Y0 + len(signals) * (CH + PAD) - PAD + 5
    cells: list[str] = []
    boundary_beats = set()
    for signal in signals:
        wave = str(signal.get("wave", ""))
        boundary_beats.update(index for index, char in enumerate(wave) if char == "|")
    for beat in range(beats + 1):
        x = X0 + beat * CW
        style = STYLE_BOUNDARY if beat in boundary_beats else STYLE_GRID
        cells.append(
            cell_edge_points(
                f"grid_{beat}",
                [(x, Y0 - 5), (x, height)],
                style,
            )
        )
    return cells


def compress_model_xml(model_xml: str) -> str:
    encoded = quote(model_xml, safe="")
    compressed = zlib.compressobj(level=9, wbits=-15)
    payload = compressed.compress(encoded.encode("utf-8")) + compressed.flush()
    return base64.b64encode(payload).decode("ascii")


def normalize_mxgraph_ids(model_xml: str) -> str:
    root = ET.fromstring(model_xml)
    graph_root = root.find("root")
    if graph_root is None:
        raise ValueError("mxGraphModel missing root element")

    cells = graph_root.findall("mxCell")
    id_map: dict[str, str] = {}
    next_id = 2
    for cell in cells:
        old_id = cell.get("id")
        if old_id is None:
            raise ValueError("mxCell missing id")
        if old_id == "0":
            id_map[old_id] = "0"
        elif old_id == "1":
            id_map[old_id] = "1"
        elif old_id not in id_map:
            id_map[old_id] = str(next_id)
            next_id += 1

    for cell in cells:
        for attr in ("id", "parent", "source", "target"):
            value = cell.get(attr)
            if value is not None and value in id_map:
                cell.set(attr, id_map[value])
    return ET.tostring(root, encoding="unicode")


def render_drawio(payload: dict) -> str:
    issues = unsupported_features(payload)
    if issues:
        formatted = ", ".join(issues)
        raise ValueError(
            "Unsupported WaveJSON/WaveDrom feature(s): "
            f"{formatted}. This converter supports only flat signal rows "
            "with name/wave/data plus an optional top-level title. Handle "
            "grouped signals, node/edge annotations, period, and phase "
            "manually so timing semantics are not silently lost."
        )

    signals = list(payload.get("signal", []))
    if not signals:
        raise ValueError("WaveJSON must contain a non-empty 'signal' array")
    beats = max(len(str(sig.get("wave", ""))) for sig in signals)
    if beats <= 0:
        raise ValueError(
            "WaveJSON must contain at least one non-empty 'wave' string"
        )
    page_width = X0 + beats * CW + 40
    page_height = Y0 + len(signals) * (CH + PAD) + 30
    cells: list[str] = [
        '        <mxCell id="0"/>',
        '        <mxCell id="1" parent="0"/>',
    ]
    cells.extend(render_boundaries(signals, beats))
    for index, signal in enumerate(signals):
        cells.extend(render_signal(signal, index))
    title = str(payload.get("title", "Timing Diagram"))
    cells.append(
        cell_vertex(
            "title",
            title,
            STYLE_TITLE,
            10,
            page_height - 25,
            page_width - 20,
            20,
        )
    )
    cells_xml = chr(10).join(cells)
    model_xml = (
        f'<mxGraphModel dx="1000" dy="700" grid="0" gridSize="10" '
        f'guides="1" tooltips="1" connect="1" arrows="1" fold="1" '
        f'page="1" pageScale="1" pageWidth="{page_width:g}" '
        f'pageHeight="{page_height:g}" math="0" shadow="0">\n'
        f'      <root>\n{cells_xml}\n      </root>\n'
        f'    </mxGraphModel>'
    )
    model_xml = normalize_mxgraph_ids(model_xml)
    payload_text = compress_model_xml(model_xml)
    return (
        '<mxfile host="app.diagrams.net" '
        'modified="2026-06-30T00:00:00.000Z" '
        'agent="Claude Code" version="24.7.17" type="device">\n'
        f'  <diagram name="{esc(title)}" id="timing-diagram">'
        f'{payload_text}</diagram>\n'
        '</mxfile>\n'
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", help="WaveJSON input file")
    parser.add_argument("output", help="Draw.io .drawio output file")
    args = parser.parse_args()

    payload = json.loads(Path(args.input).read_text(encoding="utf-8"))
    xml = render_drawio(payload)
    Path(args.output).write_text(xml, encoding="utf-8")
    print(f"Wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
