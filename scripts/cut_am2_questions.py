#!/usr/bin/env python3
"""午前Ⅱの問題冊子（ページ全体が画像）を、問と問のあいだの余白で1問ずつ切り出す。"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pymupdf

THRESH = 180
MIN_RUN = 9
MIN_BAND = 9
MAX_TEXT_LINE = 48
LEFT_SLACK = 28
PAD_X = 40
PAD_Y = 36
QUESTION_COUNT = 25


def row_left(row: bytes) -> int | None:
    run = 0
    start_x = 0
    for x, pixel in enumerate(row):
        if pixel < THRESH:
            if run == 0:
                start_x = x
            run += 1
            if run >= MIN_RUN:
                return start_x
        else:
            run = 0
    return None


def dark_runs(row: bytes) -> list[tuple[int, int]]:
    runs: list[tuple[int, int]] = []
    start = None
    for x, pixel in enumerate(row):
        if pixel < THRESH:
            if start is None:
                start = x
        elif start is not None:
            if x - start >= MIN_RUN:
                runs.append((start, x))
            start = None
    if start is not None and len(row) - start >= MIN_RUN:
        runs.append((start, len(row)))
    return runs


def text_bands(samples: bytes, width: int, height: int) -> list[tuple[int, int, int]]:
    lefts = [row_left(samples[y * width : (y + 1) * width]) for y in range(height)]
    bands: list[tuple[int, int, int]] = []
    start = None
    min_left = width
    for y in range(height + 1):
        left = lefts[y] if y < height else None
        if left is not None:
            if start is None:
                start = y
                min_left = left
            else:
                min_left = min(min_left, left)
        elif start is not None:
            if y - start >= MIN_BAND:
                bands.append((start, y, min_left))
            start = None
    return [
        band
        for band in bands
        if band[1] - band[0] <= MAX_TEXT_LINE and band[0] < int(height * 0.90)
    ]


def question_tops(samples: bytes, width: int, height: int) -> list[int]:
    bands = text_bands(samples, width, height)
    if not bands:
        return []
    page_min = min(band[2] for band in bands)
    return [band[0] for band in bands if band[2] <= page_min + LEFT_SLACK]


def is_page_number(runs: list[tuple[int, int]], width: int) -> bool:
    if not runs:
        return False
    x0 = runs[0][0]
    x1 = runs[-1][1]
    span = x1 - x0
    center = (x0 + x1) / 2
    return 40 < span < 160 and abs(center - width / 2) < 120


def footer_top(samples: bytes, width: int, height: int) -> int:
    """下端から見て、ページ番号「- n -」の上端を返す。"""
    y = height - 1
    limit = int(height * 0.75)
    while y > limit:
        runs = dark_runs(samples[y * width : (y + 1) * width])
        if is_page_number(runs, width):
            while y > limit:
                above = samples[(y - 1) * width : y * width]
                center_band = above[width // 2 - 80 : width // 2 + 80]
                if not any(pixel < THRESH for pixel in center_band):
                    break
                y -= 1
            return y
        y -= 1
    return int(height * 0.90)


def content_bounds(
    samples: bytes, width: int, y0: int, y1: int
) -> tuple[int, int, int, int] | None:
    ink_rows: list[int] = []
    for y in range(y0, y1):
        row = samples[y * width : (y + 1) * width]
        if sum(pixel < THRESH for pixel in row) >= MIN_RUN:
            ink_rows.append(y)
    if not ink_rows:
        return None
    # ページ番号の手前にある孤立した汚れは、問の本文から大きく離れているので捨てる。
    kept = [ink_rows[0]]
    for y in ink_rows[1:]:
        if y - kept[-1] > 160:
            break
        kept.append(y)
    ink_rows = kept
    columns = [0] * width
    for y in ink_rows:
        row = samples[y * width : (y + 1) * width]
        for x, pixel in enumerate(row):
            if pixel < THRESH:
                columns[x] += 1
    clusters: list[list[int]] = []
    start = None
    for x, count in enumerate(columns):
        if count >= 3:
            if start is None:
                start = x
        elif start is not None:
            clusters.append([start, x])
            start = None
    if start is not None:
        clusters.append([start, width])
    merged: list[list[int]] = []
    for cluster in clusters:
        if not merged or cluster[0] - merged[-1][1] > 40:
            merged.append(cluster)
        else:
            merged[-1][1] = cluster[1]
    main = max(merged, key=lambda item: item[1] - item[0])
    return main[0], ink_rows[0], main[1], ink_rows[-1] + 1


def load_page_image(doc: pymupdf.Document, page_index: int) -> pymupdf.Pixmap:
    xref = doc[page_index].get_images()[0][0]
    return pymupdf.Pixmap(doc, xref)


def crop_questions(pdf_path: Path, out_dir: Path) -> list[Path]:
    doc = pymupdf.open(pdf_path)
    # 表紙と裏表紙は問ではない。メモ用紙は文字がほとんどない。
    pages: list[tuple[int, pymupdf.Pixmap, list[int], int]] = []
    for page_index in range(1, doc.page_count - 1):
        pix = load_page_image(doc, page_index)
        tops = question_tops(pix.samples, pix.width, pix.height)
        if tops:
            pages.append((page_index, pix, tops, footer_top(pix.samples, pix.width, pix.height)))
    total = sum(len(tops) for _, _, tops, _ in pages)
    if total != QUESTION_COUNT:
        doc.close()
        raise SystemExit(f"問の先頭が {total} 個でした。25 個である必要があります。")

    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    number = 1
    for _, pix, tops, footer in pages:
        samples = pix.samples
        width, height = pix.width, pix.height
        limits = tops + [footer]
        for index, top in enumerate(tops):
            bottom_limit = limits[index + 1]
            bounds = content_bounds(samples, width, top, bottom_limit)
            if bounds is None:
                doc.close()
                raise SystemExit(f"問{number} の領域が空です。")
            x0, y0, x1, y1 = bounds
            x0 = max(0, x0 - PAD_X)
            y0 = max(0, y0 - PAD_Y)
            x1 = min(width, x1 + PAD_X)
            y1 = min(bottom_limit, y1 + PAD_Y)
            if index + 1 < len(tops):
                y1 = min(y1, tops[index + 1] - 8)
            crop = bytearray()
            for y in range(y0, y1):
                crop += samples[y * width + x0 : y * width + x1]
            out = pymupdf.Pixmap(pymupdf.csGRAY, x1 - x0, y1 - y0, bytes(crop), False)
            path = out_dir / f"q{number:02d}.png"
            out.save(path)
            written.append(path)
            print(f"q{number:02d} {out.width}x{out.height}")
            number += 1
    doc.close()
    return written


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("exam_dir", type=Path, help="exams/2025-r07-haru のような回ディレクトリ")
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="出力先。省略時は data/<回ディレクトリ名>/",
    )
    args = parser.parse_args()
    pdf_path = args.exam_dir / "am2-mondai.pdf"
    if not pdf_path.is_file():
        sys.exit(f"問題冊子がありません: {pdf_path}")
    out_dir = args.out or Path("data") / args.exam_dir.name
    crop_questions(pdf_path, out_dir)


if __name__ == "__main__":
    main()
