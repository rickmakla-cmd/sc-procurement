#!/usr/bin/env python3
"""Fetch SC solicitations, compute delta vs baseline, and update baseline."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import html
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Iterable

BASE_URL = (
    "https://apps.sceis.sc.gov/SCSolicitationWeb/solicitationSearch.do"
    "?searchgroup=ALL&searchstatus=O&searchlimit=500&btnSearch=on"
)
ROOT_URL = "https://apps.sceis.sc.gov"
COLUMNS = [
    "Solicitation Number",
    "Solicitation Description",
    "Purchasing Agency",
    "Submission Ending Date/Time",
    "Link to Solicitation",
]


def fetch_url(url: str, retries: int = 3, timeout: int = 60) -> str:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; sc-procurement-bot/1.0)",
            "Accept": "text/html,application/xhtml+xml",
        },
    )

    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return response.read().decode("iso-8859-1", errors="replace")
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            if attempt == retries:
                break
            time.sleep(attempt)

    if last_error is not None:
        raise RuntimeError(f"Failed to fetch URL after {retries} attempts: {url}") from last_error
    raise RuntimeError(f"Failed to fetch URL: {url}")


def extract_total_pages(html_text: str) -> int:
    pages = [int(x) for x in re.findall(r"d-49653-p=(\d+)", html_text)]
    return max(pages) if pages else 1


def strip_tags(cell_html: str) -> str:
    no_hidden = re.sub(r"<html:hidden[^>]*>", "", cell_html, flags=re.IGNORECASE)
    no_tags = re.sub(r"<[^>]+>", "", no_hidden)
    return html.unescape(no_tags).strip()


def parse_rows(page_html: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    row_pattern = re.compile(r"<tr class=\"(?:odd|even)\">(.*?)</tr>", re.DOTALL | re.IGNORECASE)
    td_pattern = re.compile(r"<td class=\"([^\"]+)\">(.*?)</td>", re.DOTALL | re.IGNORECASE)

    for row_match in row_pattern.finditer(page_html):
        row_html = row_match.group(1)
        cells = td_pattern.findall(row_html)
        if len(cells) < 4:
            continue

        number_cell = cells[0][1]
        href_match = re.search(r'href="([^"]+)"', number_cell, flags=re.IGNORECASE)
        number = strip_tags(number_cell)
        description = strip_tags(cells[1][1])
        agency = strip_tags(cells[2][1])
        submission = strip_tags(cells[3][1])

        if not number:
            continue

        link = urllib.parse.urljoin(ROOT_URL, href_match.group(1)) if href_match else ""

        rows.append(
            {
                "Solicitation Number": number,
                "Solicitation Description": description,
                "Purchasing Agency": agency,
                "Submission Ending Date/Time": submission,
                "Link to Solicitation": link,
            }
        )
    return rows


def fetch_all_rows() -> list[dict[str, str]]:
    first_page = fetch_url(BASE_URL)
    total_pages = extract_total_pages(first_page)
    all_rows = parse_rows(first_page)

    for page_num in range(2, total_pages + 1):
        page_url = f"{BASE_URL}&d-49653-p={page_num}"
        page_html = fetch_url(page_url)
        all_rows.extend(parse_rows(page_html))

    deduped: dict[str, dict[str, str]] = {}
    for row in all_rows:
        deduped[row["Solicitation Number"]] = row
    return list(deduped.values())


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return [{k: (v or "") for k, v in row.items()} for row in reader]


def write_csv(path: Path, rows: Iterable[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def compute_delta(current: list[dict[str, str]], baseline: list[dict[str, str]]) -> list[dict[str, str]]:
    baseline_numbers = {row["Solicitation Number"] for row in baseline}
    delta = [row for row in current if row["Solicitation Number"] not in baseline_numbers]
    delta.sort(key=lambda row: row["Solicitation Number"], reverse=True)
    return delta


def reset_baseline(path: Path) -> None:
    write_csv(path, [])


def main() -> int:
    parser = argparse.ArgumentParser(description="SC procurement delta tracker")
    parser.add_argument("--baseline", default="data/baseline.csv", help="Baseline CSV path")
    parser.add_argument("--output-dir", default="outputs", help="Directory for delta CSV files")
    parser.add_argument("--reset-baseline", action="store_true", help="Reset baseline CSV to empty and exit")
    args = parser.parse_args()

    baseline_path = Path(args.baseline)
    output_dir = Path(args.output_dir)

    if args.reset_baseline:
        reset_baseline(baseline_path)
        print(f"Baseline reset: {baseline_path.resolve()}")
        return 0

    current_rows = fetch_all_rows()
    baseline_rows = read_csv_rows(baseline_path)
    delta_rows = compute_delta(current_rows, baseline_rows)

    timestamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    delta_path = output_dir / f"delta_{timestamp}.csv"
    write_csv(delta_path, delta_rows)
    write_csv(baseline_path, current_rows)

    print(f"Delta CSV: {delta_path.resolve()}")
    print(f"New solicitations: {len(delta_rows)}")
    print(f"Baseline updated: {baseline_path.resolve()} ({len(current_rows)} rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
