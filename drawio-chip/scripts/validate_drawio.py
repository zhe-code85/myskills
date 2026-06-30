#!/usr/bin/env python3
"""Validate Draw.io (.drawio) XML produced by drawio-chip.

Supports both uncompressed diagrams containing mxGraphModel XML and standard
compressed diagrams.net payloads inside <diagram> text.
"""

from __future__ import annotations

import argparse
import base64
import sys
import urllib.parse
import xml.etree.ElementTree as ET
import zlib
from pathlib import Path
from typing import Tuple

Point = Tuple[float, float]
Rect = Tuple[float, float, float, float]


class ValidationError(Exception):
    """Raised when a Draw.io file violates required structure."""


def read_input(path: str) -> str:
    if path == "-":
        return sys.stdin.read()
    return Path(path).read_text(encoding="utf-8")


def parse_xml(text: str) -> ET.Element:
    try:
        return ET.fromstring(text)
    except ET.ParseError as exc:
        raise ValidationError(f"XML parse failed: {exc}") from exc


def decode_compressed_diagram_payload(payload: str, graph_index: int) -> ET.Element:
    """Decode diagrams.net's deflate+base64+urlencoded diagram payload."""
    try:
        compressed = base64.b64decode(payload)
        encoded_xml = zlib.decompress(compressed, wbits=-15).decode("utf-8")
        xml = urllib.parse.unquote(encoded_xml)
        model = ET.fromstring(xml)
    except Exception as exc:  # noqa: BLE001 - validation must report decode details.
        raise ValidationError(f"diagram {graph_index}: compressed payload decode failed: {exc}") from exc
    if model.tag != "mxGraphModel":
        raise ValidationError(
            f"diagram {graph_index}: compressed payload must decode to mxGraphModel, got {model.tag!r}"
        )
    return model


def get_graph_models(root: ET.Element) -> list[ET.Element]:
    if root.tag == "mxGraphModel":
        return [root]
    if root.tag != "mxfile":
        raise ValidationError(f"root element must be mxfile or mxGraphModel, got {root.tag!r}")
    models: list[ET.Element] = []
    for index, diagram in enumerate(root.findall("diagram"), start=1):
        if diagram.text and diagram.text.strip():
            models.append(decode_compressed_diagram_payload(diagram.text.strip(), index))
            continue
        child_model = diagram.find("mxGraphModel")
        if child_model is not None:
            models.append(child_model)
    if not models:
        raise ValidationError("no diagram payload found under mxfile")
    return models


def parse_style(style: str | None) -> tuple[set[str], dict[str, str]]:
    """Split Draw.io's semicolon style string into flags and key/value pairs."""
    flags: set[str] = set()
    values: dict[str, str] = {}
    for raw_part in (style or "").split(";"):
        part = raw_part.strip()
        if not part:
            continue
        if "=" in part:
            key, value = part.split("=", 1)
            values[key.strip()] = value.strip()
        else:
            flags.add(part)
    return flags, values


def is_text_vertex(style: str | None) -> bool:
    flags, values = parse_style(style)
    return "text" in flags or values.get("shape") == "text"


def validate_transparent_text_style(cell_id: str, style: str | None, graph_index: int) -> None:
    _, values = parse_style(style)
    for key in ("fillColor", "labelBackgroundColor"):
        value = values.get(key)
        if value is not None and value.lower() != "none":
            raise ValidationError(
                f"graph {graph_index}: text vertex {cell_id!r} uses {key}={value!r}; "
                "use fillColor=none/labelBackgroundColor=none and move labels beside wires"
            )


def parse_float(value: str | None, *, default: float, context: str) -> float:
    if value is None:
        return default
    try:
        return float(value)
    except ValueError as exc:
        raise ValidationError(f"{context}: non-numeric value {value!r}") from exc


def get_vertex_rect(cell: ET.Element, graph_index: int) -> Rect | None:
    geom = cell.find("mxGeometry")
    if geom is None:
        return None
    cell_id = cell.get("id", "<missing>")
    return (
        parse_float(geom.get("x"), default=0.0, context=f"graph {graph_index}: vertex {cell_id!r} x"),
        parse_float(geom.get("y"), default=0.0, context=f"graph {graph_index}: vertex {cell_id!r} y"),
        parse_float(geom.get("width"), default=0.0, context=f"graph {graph_index}: vertex {cell_id!r} width"),
        parse_float(geom.get("height"), default=0.0, context=f"graph {graph_index}: vertex {cell_id!r} height"),
    )


def anchor_from_vertex(
    cell_id: str | None,
    style_values: dict[str, str],
    rects: dict[str, Rect],
    *,
    prefix: str,
    graph_index: int,
    edge_id: str,
) -> Point | None:
    if not cell_id:
        return None
    rect = rects.get(cell_id)
    if rect is None:
        return None
    x, y, width, height = rect
    default_x = 1.0 if prefix == "exit" else 0.0
    rel_x = parse_float(
        style_values.get(f"{prefix}X"),
        default=default_x,
        context=f"graph {graph_index}: edge {edge_id!r} {prefix}X",
    )
    rel_y = parse_float(
        style_values.get(f"{prefix}Y"),
        default=0.5,
        context=f"graph {graph_index}: edge {edge_id!r} {prefix}Y",
    )
    return x + width * rel_x, y + height * rel_y


def geometry_point(geom: ET.Element | None, point_kind: str, *, graph_index: int, edge_id: str) -> Point | None:
    if geom is None:
        return None
    point = geom.find(f"mxPoint[@as='{point_kind}']")
    if point is None:
        return None
    return (
        parse_float(point.get("x"), default=0.0, context=f"graph {graph_index}: edge {edge_id!r} {point_kind} x"),
        parse_float(point.get("y"), default=0.0, context=f"graph {graph_index}: edge {edge_id!r} {point_kind} y"),
    )


def edge_polyline_points(edge: ET.Element, rects: dict[str, Rect], graph_index: int) -> list[Point]:
    edge_id = edge.get("id", "<missing>")
    _, style_values = parse_style(edge.get("style"))
    geom = edge.find("mxGeometry")

    points: list[Point] = []
    source_point = geometry_point(geom, "sourcePoint", graph_index=graph_index, edge_id=edge_id)
    if source_point is not None:
        points.append(source_point)
    else:
        source_anchor = anchor_from_vertex(
            edge.get("source"),
            style_values,
            rects,
            prefix="exit",
            graph_index=graph_index,
            edge_id=edge_id,
        )
        if source_anchor is not None:
            points.append(source_anchor)

    if geom is not None:
        array = geom.find("Array[@as='points']")
        if array is not None:
            for point_index, point in enumerate(array.findall("mxPoint")):
                points.append(
                    (
                        parse_float(
                            point.get("x"),
                            default=0.0,
                            context=f"graph {graph_index}: edge {edge_id!r} points[{point_index}] x",
                        ),
                        parse_float(
                            point.get("y"),
                            default=0.0,
                            context=f"graph {graph_index}: edge {edge_id!r} points[{point_index}] y",
                        ),
                    )
                )

    target_point = geometry_point(geom, "targetPoint", graph_index=graph_index, edge_id=edge_id)
    if target_point is not None:
        points.append(target_point)
    else:
        target_anchor = anchor_from_vertex(
            edge.get("target"),
            style_values,
            rects,
            prefix="entry",
            graph_index=graph_index,
            edge_id=edge_id,
        )
        if target_anchor is not None:
            points.append(target_anchor)

    return points


def segment_intersects_rect(p1: Point, p2: Point, rect: Rect, clearance: float = 0.0) -> bool:
    x, y, width, height = rect
    x -= clearance
    y -= clearance
    width += clearance * 2
    height += clearance * 2
    x1, y1 = p1
    x2, y2 = p2

    if x1 == x2:
        return x <= x1 <= x + width and max(min(y1, y2), y) <= min(max(y1, y2), y + height)
    if y1 == y2:
        return y <= y1 <= y + height and max(min(x1, x2), x) <= min(max(x1, x2), x + width)

    # Conservative fallback for diagonal or auto-routed approximations.
    return not (
        max(x1, x2) < x
        or min(x1, x2) > x + width
        or max(y1, y2) < y
        or min(y1, y2) > y + height
    )


def validate_no_text_line_overlap(
    cells: list[ET.Element], graph_index: int, *, clearance: float = 0.0
) -> None:
    vertex_rects = {
        cell.get("id", ""): rect
        for cell in cells
        if cell.get("vertex") == "1"
        for rect in [get_vertex_rect(cell, graph_index)]
        if rect is not None
    }
    text_rects = {
        cell_id: vertex_rects[cell_id]
        for cell_id, cell in ((cell.get("id", ""), cell) for cell in cells)
        if cell_id in vertex_rects and cell.get("vertex") == "1" and is_text_vertex(cell.get("style"))
    }

    for edge in cells:
        if edge.get("edge") != "1":
            continue
        edge_id = edge.get("id", "<missing>")
        points = edge_polyline_points(edge, vertex_rects, graph_index)
        for p1, p2 in zip(points, points[1:]):
            for text_id, rect in text_rects.items():
                if text_id in {edge.get("source"), edge.get("target")}:
                    continue
                if segment_intersects_rect(p1, p2, rect, clearance=clearance):
                    raise ValidationError(
                        f"graph {graph_index}: text vertex {text_id!r} overlaps edge {edge_id!r}; "
                        "move the label into whitespace or reroute the edge"
                    )


def is_numeric_id(value: str) -> bool:
    return value.isdigit()


def validate_graph_model(
    model: ET.Element,
    index: int,
    *,
    no_edge_labels: bool = False,
    transparent_text_labels: bool = False,
    no_text_line_overlap: bool = False,
    allow_non_numeric_ids: bool = False,
) -> tuple[int, int]:
    root = model.find("root")
    if root is None:
        raise ValidationError(f"graph {index}: missing <root> under mxGraphModel")

    cells = root.findall("mxCell")
    if not cells:
        raise ValidationError(f"graph {index}: no mxCell elements found")

    ids: dict[str, ET.Element] = {}
    for cell in cells:
        cell_id = cell.get("id")
        if not cell_id:
            raise ValidationError(f"graph {index}: mxCell missing id")
        if not allow_non_numeric_ids and not is_numeric_id(cell_id):
            raise ValidationError(f"graph {index}: mxCell id {cell_id!r} must be numeric")
        if cell_id in ids:
            raise ValidationError(f"graph {index}: duplicate mxCell id {cell_id!r}")
        ids[cell_id] = cell

    if "0" not in ids or "1" not in ids:
        raise ValidationError(f"graph {index}: required root cells id='0' and id='1' are missing")
    if ids["1"].get("parent") != "0":
        raise ValidationError(f"graph {index}: root cell id='1' must have parent='0'")

    edge_ids = {cell_id for cell_id, cell in ids.items() if cell.get("edge") == "1"}
    vertices = 0
    edges = 0
    for cell in cells:
        cell_id = cell.get("id", "<missing>")
        is_vertex = cell.get("vertex") == "1"
        is_edge = cell.get("edge") == "1"
        if is_vertex and is_edge:
            raise ValidationError(f"graph {index}: mxCell {cell_id!r} cannot be both vertex and edge")

        if is_vertex:
            vertices += 1
            if no_edge_labels and cell.get("parent") in edge_ids:
                raise ValidationError(
                    f"graph {index}: vertex {cell_id!r} is attached to an edge; "
                    "use a standalone text vertex with parent='1' for labels"
                )
            if cell.get("parent") is None:
                raise ValidationError(f"graph {index}: vertex {cell_id!r} missing parent")
            parent = cell.get("parent", "")
            if not allow_non_numeric_ids and not is_numeric_id(parent):
                raise ValidationError(f"graph {index}: vertex {cell_id!r} parent must be numeric")
            if parent not in ids:
                raise ValidationError(
                    f"graph {index}: vertex {cell_id!r} parent references missing id {parent!r}"
                )
            geom = cell.find("mxGeometry")
            if geom is None or geom.get("as") != "geometry":
                raise ValidationError(f"graph {index}: vertex {cell_id!r} missing mxGeometry as='geometry'")
            for attr in ("width", "height"):
                value = geom.get(attr)
                if value is None:
                    continue
                try:
                    if float(value) < 0:
                        raise ValidationError(
                            f"graph {index}: vertex {cell_id!r} has negative {attr}"
                        )
                except ValueError as exc:
                    raise ValidationError(
                        f"graph {index}: vertex {cell_id!r} has non-numeric {attr}={value!r}"
                    ) from exc
            if transparent_text_labels and is_text_vertex(cell.get("style")):
                validate_transparent_text_style(cell_id, cell.get("style"), index)

        if is_edge:
            edges += 1
            if no_edge_labels and (cell.get("value") or "").strip():
                raise ValidationError(
                    f"graph {index}: edge {cell_id!r} has text in value; "
                    "use a separate text vertex for labels"
                )
            if cell.get("parent") is None:
                raise ValidationError(f"graph {index}: edge {cell_id!r} missing parent")
            parent = cell.get("parent", "")
            if not allow_non_numeric_ids and not is_numeric_id(parent):
                raise ValidationError(f"graph {index}: edge {cell_id!r} parent must be numeric")
            if parent not in ids:
                raise ValidationError(
                    f"graph {index}: edge {cell_id!r} parent references missing id {parent!r}"
                )
            for endpoint in ("source", "target"):
                ref = cell.get(endpoint)
                if ref is not None:
                    if not allow_non_numeric_ids and not is_numeric_id(ref):
                        raise ValidationError(
                            f"graph {index}: edge {cell_id!r} {endpoint} reference {ref!r} must be numeric"
                        )
                    if ref not in ids:
                        raise ValidationError(
                            f"graph {index}: edge {cell_id!r} {endpoint} references missing id {ref!r}"
                        )
            geom = cell.find("mxGeometry")
            if geom is None or geom.get("as") != "geometry":
                raise ValidationError(f"graph {index}: edge {cell_id!r} missing mxGeometry as='geometry'")

    if no_text_line_overlap:
        validate_no_text_line_overlap(cells, index)

    return vertices, edges


def validate_drawio(
    text: str,
    *,
    no_edge_labels: bool = False,
    transparent_text_labels: bool = False,
    no_text_line_overlap: bool = False,
    allow_non_numeric_ids: bool = False,
) -> tuple[int, int, int]:
    root = parse_xml(text)
    models = get_graph_models(root)
    total_vertices = 0
    total_edges = 0
    for index, model in enumerate(models, start=1):
        vertices, edges = validate_graph_model(
            model,
            index,
            no_edge_labels=no_edge_labels,
            transparent_text_labels=transparent_text_labels,
            no_text_line_overlap=no_text_line_overlap,
            allow_non_numeric_ids=allow_non_numeric_ids,
        )
        total_vertices += vertices
        total_edges += edges
    return len(models), total_vertices, total_edges


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--no-edge-labels",
        action="store_true",
        help="fail when edge cells or edge-attached label vertices store text",
    )
    parser.add_argument(
        "--transparent-text-labels",
        action="store_true",
        help="fail when standalone text vertices use opaque label backgrounds",
    )
    parser.add_argument(
        "--no-text-line-overlap",
        action="store_true",
        help="fail when standalone text vertices intersect edge polylines",
    )
    parser.add_argument(
        "--allow-non-numeric-cell-ids",
        action="store_true",
        help="allow non-numeric mxCell id/source/target/parent values; disabled by default because Draw.io clients can fail on string cell ids",
    )
    parser.add_argument("path", help=".drawio file path, or '-' to read XML from stdin")
    args = parser.parse_args(argv)

    try:
        text = read_input(args.path)
        graphs, vertices, edges = validate_drawio(
            text,
            no_edge_labels=args.no_edge_labels,
            transparent_text_labels=args.transparent_text_labels,
            no_text_line_overlap=args.no_text_line_overlap,
            allow_non_numeric_ids=args.allow_non_numeric_cell_ids,
        )
    except (OSError, ValidationError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(f"OK: {graphs} graph(s), {vertices} vertex cell(s), {edges} edge cell(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
