"""Create side-by-side visual comparisons for rendered document PNGs."""

from __future__ import annotations

import argparse
import json
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


def compare(template_render_dir: Path, draft_render_dir: Path, out_dir: Path) -> dict:
    template_pages = page_pngs(template_render_dir)
    draft_pages = page_pngs(draft_render_dir)
    compared = min(len(template_pages), len(draft_pages))
    out_dir.mkdir(parents=True, exist_ok=True)
    pages = []
    for index in range(compared):
        template_png = template_pages[index]
        draft_png = draft_pages[index]
        side_by_side = out_dir / f"page-{index + 1:03d}-side-by-side.png"
        template_pix = pixmap_for(template_png)
        draft_pix = pixmap_for(draft_png)
        write_side_by_side(
            template_png,
            draft_png,
            side_by_side,
            label_left=f"template {template_png.name}",
            label_right=f"draft {draft_png.name}",
        )
        pages.append(
            {
                "page": index + 1,
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
        "page_count_template": len(template_pages),
        "page_count_draft": len(draft_pages),
        "page_count_compared": compared,
        "pages": pages,
    }
    (out_dir / "visual_comparison.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    lines = [
        "# Visual Comparison",
        "",
        f"- Template pages: {len(template_pages)}",
        f"- Draft pages: {len(draft_pages)}",
        f"- Compared pages: {compared}",
        "",
    ]
    for page in pages:
        lines.append(f"- Page {page['page']}: mean_abs_diff={page['mean_abs_diff']}, side_by_side={Path(page['side_by_side_png']).name}")
    (out_dir / "visual_comparison.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Compare rendered PNG pages and create side-by-side visual review images.")
    parser.add_argument("--template-render-dir", type=Path, required=True)
    parser.add_argument("--draft-render-dir", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = compare(args.template_render_dir, args.draft_render_dir, args.out_dir)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(f"Compared pages: {result['page_count_compared']}")
    print(f"Summary: {args.out_dir / 'visual_comparison.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
