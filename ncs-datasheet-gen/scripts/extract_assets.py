"""Extract reusable media assets from a DOCX source document."""

from __future__ import annotations

import argparse
import json
import re
import sys
import zipfile
from pathlib import Path


MEDIA_PREFIX = "word/media/"


def should_copy(name: str, include: re.Pattern[str] | None, exclude: re.Pattern[str] | None) -> bool:
    base = Path(name).name
    if include and not include.search(base):
        return False
    if exclude and exclude.search(base):
        return False
    return True


def unique_path(out_dir: Path, filename: str) -> Path:
    candidate = out_dir / filename
    if not candidate.exists():
        return candidate
    stem = candidate.stem
    suffix = candidate.suffix
    index = 2
    while True:
        candidate = out_dir / f"{stem}_{index}{suffix}"
        if not candidate.exists():
            return candidate
        index += 1


def extract_assets(source: Path, out_dir: Path, manifest: Path, include: str | None, exclude: str | None) -> dict:
    if not source.exists():
        raise FileNotFoundError(source)
    include_re = re.compile(include) if include else None
    exclude_re = re.compile(exclude) if exclude else None
    out_dir.mkdir(parents=True, exist_ok=True)
    copied: list[dict[str, str | int]] = []
    with zipfile.ZipFile(source) as package:
        for name in package.namelist():
            if not name.startswith(MEDIA_PREFIX) or name.endswith("/"):
                continue
            if not should_copy(name, include_re, exclude_re):
                continue
            target = unique_path(out_dir, Path(name).name)
            data = package.read(name)
            target.write_bytes(data)
            copied.append({"source": name, "output": str(target), "bytes": len(data)})
    data = {
        "source_docx": str(source),
        "out_dir": str(out_dir),
        "include_regex": include,
        "exclude_regex": exclude,
        "copied_count": len(copied),
        "assets": copied,
    }
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    return data


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Extract DOCX media assets with optional include/exclude filters.")
    parser.add_argument("--source", type=Path, required=True, help="Existing company product DOCX")
    parser.add_argument("--out-dir", type=Path, required=True, help="Directory for extracted media")
    parser.add_argument("--manifest", type=Path, required=True, help="Output JSON manifest")
    parser.add_argument("--include-regex", help="Only copy media filenames matching this regex")
    parser.add_argument("--exclude-regex", help="Skip media filenames matching this regex")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = extract_assets(args.source, args.out_dir, args.manifest, args.include_regex, args.exclude_regex)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(f"Copied {result['copied_count']} assets to {args.out_dir}")
    print(f"Manifest: {args.manifest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
