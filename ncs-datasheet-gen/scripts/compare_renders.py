"""Create side-by-side visual comparisons for rendered document PNGs."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


def import_fitz():
    try:
        import fitz  # type: ignore
    except Exception as exc:
        raise RuntimeError("PyMuPDF is required for render comparison. Install PyMuPDF.") from exc
    return fitz


def page_pngs(render_dir: Path) -> list[Path]:
    return sorted(render_dir.glob("page-*.png"))


def safe_label(value: str) -> str:
    label = re.sub(r"[^A-Za-z0-9_.-]+", "-", value.strip())
    return label.strip("-") or "page-role"


def parse_pair(raw: str) -> dict:
    if "=" not in raw or ":" not in raw:
        raise argparse.ArgumentTypeError("expected ROLE=TEMPLATE_PAGE:DRAFT_PAGE")
    role, pages = raw.split("=", 1)
    template_page, draft_page = pages.split(":", 1)
    try:
        template_number = int(template_page)
        draft_number = int(draft_page)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("page numbers must be integers") from exc
    if template_number < 1 or draft_number < 1:
        raise argparse.ArgumentTypeError("page numbers are 1-based and must be positive")
    role = role.strip()
    if not role:
        raise argparse.ArgumentTypeError("role must not be empty")
    return {"role": role, "template_page": template_number, "draft_page": draft_number}


def load_pairs(path: Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict):
        data = data.get("pairs") or data.get("page_role_mapping") or data.get("pages")
    if not isinstance(data, list):
        raise ValueError("pairs JSON must be a list or contain pairs/page_role_mapping/pages list")
    pairs = []
    for index, item in enumerate(data, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"pair {index} must be an object")
        role = str(item.get("role") or item.get("layout_role") or f"role-{index}")
        template_page = int(item.get("template_page") or item.get("template") or item.get("left_page"))
        draft_page = int(item.get("draft_page") or item.get("draft") or item.get("right_page"))
        if template_page < 1 or draft_page < 1:
            raise ValueError(f"pair {index} uses invalid 1-based page numbers")
        pairs.append({"role": role, "template_page": template_page, "draft_page": draft_page})
    return pairs


def pixmap_for(path: Path):
    fitz = import_fitz()
    document = fitz.open(path)
    try:
        return document[0].get_pixmap(alpha=False)
    finally:
        document.close()


def mean_abs_diff(left, right) -> float:
    if left.width != right.width or left.height != right.height or left.n != right.n:
        return 255.0
    left_samples = left.samples
    right_samples = right.samples
    if not left_samples:
        return 0.0
    total = sum(abs(a - b) for a, b in zip(left_samples, right_samples))
    return total / len(left_samples)


def write_side_by_side(template_png: Path, draft_png: Path, output_png: Path, *, label_left: str, label_right: str) -> None:
    fitz = import_fitz()
    left = pixmap_for(template_png)
    right = pixmap_for(draft_png)
    gutter = 24
    label_height = 24
    width = left.width + right.width + gutter
    height = max(left.height, right.height) + label_height
    document = fitz.open()
    page = document.new_page(width=width, height=height)
    page.insert_text((0, 16), label_left, fontsize=10, fontname="helv", color=(0.35, 0, 0))
    page.insert_text((left.width + gutter, 16), label_right, fontsize=10, fontname="helv", color=(0, 0.2, 0.45))
    page.insert_image(fitz.Rect(0, label_height, left.width, label_height + left.height), filename=str(template_png))
    page.insert_image(
        fitz.Rect(left.width + gutter, label_height, left.width + gutter + right.width, label_height + right.height),
        filename=str(draft_png),
    )
    output_png.parent.mkdir(parents=True, exist_ok=True)
    page.get_pixmap(alpha=False).save(output_png)
    document.close()


def compare(template_render_dir: Path, draft_render_dir: Path, out_dir: Path, pairs: list[dict] | None = None) -> dict:
    template_pages = page_pngs(template_render_dir)
    draft_pages = page_pngs(draft_render_dir)
    if pairs is None:
        compared = min(len(template_pages), len(draft_pages))
        pairs = [
            {"role": f"page-{index + 1:03d}", "template_page": index + 1, "draft_page": index + 1}
            for index in range(compared)
        ]
        comparison_mode = "page_index"
    else:
        comparison_mode = "page_role"
        compared = len(pairs)
    out_dir.mkdir(parents=True, exist_ok=True)
    pages = []
    for index, pair in enumerate(pairs, start=1):
        template_page_number = pair["template_page"]
        draft_page_number = pair["draft_page"]
        if template_page_number > len(template_pages):
            raise ValueError(f"template page {template_page_number} for role {pair['role']} is not rendered")
        if draft_page_number > len(draft_pages):
            raise ValueError(f"draft page {draft_page_number} for role {pair['role']} is not rendered")
        template_png = template_pages[template_page_number - 1]
        draft_png = draft_pages[draft_page_number - 1]
        role_label = safe_label(str(pair["role"]))
        side_by_side = out_dir / f"{index:03d}-{role_label}-template-{template_page_number:03d}-draft-{draft_page_number:03d}-side-by-side.png"
        template_pix = pixmap_for(template_png)
        draft_pix = pixmap_for(draft_png)
        write_side_by_side(
            template_png,
            draft_png,
            side_by_side,
            label_left=f"template {pair['role']} {template_png.name}",
            label_right=f"draft {pair['role']} {draft_png.name}",
        )
        pages.append(
            {
                "role": pair["role"],
                "template_page": template_page_number,
                "draft_page": draft_page_number,
                "template_png": str(template_png.resolve()),
                "draft_png": str(draft_png.resolve()),
                "side_by_side_png": str(side_by_side.resolve()),
                "template_size": [template_pix.width, template_pix.height],
                "draft_size": [draft_pix.width, draft_pix.height],
                "mean_abs_diff": round(mean_abs_diff(template_pix, draft_pix), 4),
            }
        )
    result = {
        "template_render_dir": str(template_render_dir.resolve()),
        "draft_render_dir": str(draft_render_dir.resolve()),
        "comparison_mode": comparison_mode,
        "page_count_template": len(template_pages),
        "page_count_draft": len(draft_pages),
        "page_count_compared": compared,
        "pages": pages,
    }
    (out_dir / "visual_comparison.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    lines = [
        "# Visual Comparison",
        "",
        f"- Comparison mode: {comparison_mode}",
        f"- Template pages: {len(template_pages)}",
        f"- Draft pages: {len(draft_pages)}",
        f"- Compared pages: {compared}",
        "",
    ]
    for page in pages:
        lines.append(
            "- "
            f"{page['role']}: template_page={page['template_page']}, draft_page={page['draft_page']}, "
            f"mean_abs_diff={page['mean_abs_diff']}, side_by_side={Path(page['side_by_side_png']).name}"
        )
    (out_dir / "visual_comparison.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Compare rendered PNG pages and create side-by-side visual review images.")
    parser.add_argument("--template-render-dir", type=Path, required=True)
    parser.add_argument("--draft-render-dir", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument(
        "--pair",
        action="append",
        type=parse_pair,
        help="Role-based page pair as ROLE=TEMPLATE_PAGE:DRAFT_PAGE; repeatable",
    )
    parser.add_argument("--pairs-json", type=Path, help="JSON list of role/template_page/draft_page objects")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        pairs = []
        if args.pairs_json:
            pairs.extend(load_pairs(args.pairs_json))
        if args.pair:
            pairs.extend(args.pair)
        result = compare(args.template_render_dir, args.draft_render_dir, args.out_dir, pairs or None)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(f"Compared pages: {result['page_count_compared']} ({result['comparison_mode']})")
    print(f"Summary: {args.out_dir / 'visual_comparison.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
