#!/usr/bin/env python3
"""Generate repository artifacts from data/companies.csv."""

from __future__ import annotations

import argparse
import csv
import difflib
import json
import re
import sys
from collections import OrderedDict
from pathlib import Path
from urllib.parse import parse_qsl, urlparse


ROOT = Path(__file__).resolve().parents[1]
README_PATH = ROOT / "README.md"
CSV_PATH = ROOT / "data" / "companies.csv"
JSON_PATH = ROOT / "data" / "companies.json"

GENERATED_START = "<!-- LISTING:START -->"
GENERATED_END = "<!-- LISTING:END -->"

REQUIRED_FIELDS = ["rank", "category", "company", "ai_employee_angle", "link"]
BLOCKED_QUERY_PREFIXES = ("utm_",)
BLOCKED_QUERY_KEYS = {"aff", "affiliate", "ref", "referrer", "source"}


def markdown_anchor(heading: str) -> str:
    anchor = heading.strip().lower()
    anchor = re.sub(r"[^\w\s-]", "", anchor)
    anchor = re.sub(r"\s+", "-", anchor)
    return anchor


def markdown_cell(value: str) -> str:
    return " ".join(value.split()).replace("|", r"\|")


def validate_url(value: str, line_number: int) -> None:
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError(
            f"{CSV_PATH.relative_to(ROOT)}:{line_number} link must be an absolute HTTP(S) URL"
        )

    blocked = []
    for key, _value in parse_qsl(parsed.query, keep_blank_values=True):
        normalized = key.lower()
        if normalized in BLOCKED_QUERY_KEYS or normalized.startswith(BLOCKED_QUERY_PREFIXES):
            blocked.append(key)

    if blocked:
        raise ValueError(
            f"{CSV_PATH.relative_to(ROOT)}:{line_number} link contains tracking or affiliate "
            f"parameters: {', '.join(blocked)}"
        )


def read_companies() -> list[dict[str, str]]:
    with CSV_PATH.open(newline="", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        if reader.fieldnames != REQUIRED_FIELDS:
            raise ValueError(
                f"{CSV_PATH.relative_to(ROOT)} must have headers: {', '.join(REQUIRED_FIELDS)}"
            )

        rows = []
        raw_ranks = []
        seen_ranks = set()
        seen_companies = set()
        completed_categories = set()
        active_category = None
        for line_number, row in enumerate(reader, start=2):
            normalized = {key: (row.get(key) or "").strip() for key in REQUIRED_FIELDS}
            missing = [key for key, value in normalized.items() if not value]
            if missing:
                raise ValueError(
                    f"{CSV_PATH.relative_to(ROOT)}:{line_number} missing {', '.join(missing)}"
                )

            try:
                rank = int(normalized["rank"])
            except ValueError as error:
                raise ValueError(
                    f"{CSV_PATH.relative_to(ROOT)}:{line_number} rank must be an integer"
                ) from error

            if rank in seen_ranks:
                raise ValueError(
                    f"{CSV_PATH.relative_to(ROOT)}:{line_number} duplicate rank {rank}"
                )
            seen_ranks.add(rank)

            company_key = normalized["company"].casefold()
            if company_key in seen_companies:
                raise ValueError(
                    f"{CSV_PATH.relative_to(ROOT)}:{line_number} duplicate company "
                    f"{normalized['company']}"
                )
            seen_companies.add(company_key)

            category = normalized["category"]
            if active_category is None:
                active_category = category
            elif category != active_category:
                completed_categories.add(active_category)
                if category in completed_categories:
                    raise ValueError(
                        f"{CSV_PATH.relative_to(ROOT)}:{line_number} category {category!r} "
                        "must be in one contiguous block"
                    )
                active_category = category

            validate_url(normalized["link"], line_number)
            raw_ranks.append(rank)
            rows.append(normalized)

    expected_ranks = list(range(1, len(rows) + 1))
    if raw_ranks != expected_ranks:
        raise ValueError(
            f"{CSV_PATH.relative_to(ROOT)} ranks must be contiguous and sorted from 1 "
            f"to {len(rows)}"
        )

    return rows


def category_groups(rows: list[dict[str, str]]) -> OrderedDict[str, list[dict[str, str]]]:
    groups: OrderedDict[str, list[dict[str, str]]] = OrderedDict()
    for row in rows:
        groups.setdefault(row["category"], []).append(row)
    return groups


def generated_contents(groups: OrderedDict[str, list[dict[str, str]]]) -> str:
    lines = [
        "- [Curation Criteria](#curation-criteria)",
        "- [Domain Counts](#domain-counts)",
    ]
    lines.extend(
        f"- [{category}](#{markdown_anchor(category)})" for category in groups.keys()
    )
    lines.extend(
        [
            "- [Data](#data)",
            "- [Contributing](#contributing)",
            "- [Roadmap](#roadmap)",
            "- [License](#license)",
        ]
    )
    return "\n".join(lines)


def generated_listing(rows: list[dict[str, str]]) -> str:
    groups = category_groups(rows)
    lines = [
        GENERATED_START,
        "<!-- This section is generated from data/companies.csv. Do not edit it by hand. -->",
        "",
        "## Contents",
        "",
        generated_contents(groups),
        "",
        "## Domain Counts",
        "",
    ]

    for category, category_rows in groups.items():
        lines.append(f"- {category}: {len(category_rows)}")
    lines.extend(["", f"Total: {len(rows)}", ""])

    for category, category_rows in groups.items():
        lines.extend(
            [
                f"## {category}",
                "",
                "| # | Company | AI employee angle | Link |",
                "|---:|---|---|---|",
            ]
        )
        for row in category_rows:
            lines.append(
                "| {rank} | {company} | {angle} | {link} |".format(
                    rank=markdown_cell(row["rank"]),
                    company=markdown_cell(row["company"]),
                    angle=markdown_cell(row["ai_employee_angle"]),
                    link=markdown_cell(row["link"]),
                )
            )
        lines.append("")

    lines.append(GENERATED_END)
    return "\n".join(lines)


def generated_summary(rows: list[dict[str, str]]) -> tuple[int, int]:
    return len(rows), len(category_groups(rows))


def render_json(rows: list[dict[str, str]]) -> str:
    records = [
        {
            "rank": int(row["rank"]),
            "category": row["category"],
            "company": row["company"],
            "ai_employee_angle": row["ai_employee_angle"],
            "link": row["link"],
        }
        for row in rows
    ]
    return json.dumps(records, indent=2, ensure_ascii=False) + "\n"


def render_readme(readme: str, rows: list[dict[str, str]]) -> str:
    total, categories = generated_summary(rows)
    rendered = re.sub(r"Companies tracked: \d+", f"Companies tracked: {total}", readme)
    rendered = re.sub(r"Categories: \d+", f"Categories: {categories}", rendered)

    start = rendered.find(GENERATED_START)
    end = rendered.find(GENERATED_END)
    replacement = generated_listing(rows)

    if start == -1 or end == -1:
        raise ValueError(
            f"{README_PATH.relative_to(ROOT)} must contain {GENERATED_START} and {GENERATED_END}"
        )

    end += len(GENERATED_END)
    rendered = rendered[:start] + replacement + rendered[end:]
    return rendered.rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="fail if README.md is not already generated from data/companies.csv",
    )
    args = parser.parse_args()

    rows = read_companies()
    current = README_PATH.read_text(encoding="utf-8")
    rendered = render_readme(current, rows)
    rendered_json = render_json(rows)

    if args.check:
        failed = False
        if current != rendered:
            diff = difflib.unified_diff(
                current.splitlines(),
                rendered.splitlines(),
                fromfile="README.md",
                tofile="README.md.generated",
                lineterm="",
            )
            print("\n".join(diff), file=sys.stderr)
            failed = True

        current_json = JSON_PATH.read_text(encoding="utf-8") if JSON_PATH.exists() else ""
        if current_json != rendered_json:
            diff = difflib.unified_diff(
                current_json.splitlines(),
                rendered_json.splitlines(),
                fromfile="data/companies.json",
                tofile="data/companies.json.generated",
                lineterm="",
            )
            print("\n".join(diff), file=sys.stderr)
            failed = True

        if failed:
            return 1
        print("Generated artifacts are up to date")
        return 0

    README_PATH.write_text(rendered, encoding="utf-8")
    JSON_PATH.write_text(rendered_json, encoding="utf-8")
    print(
        f"Generated README.md and data/companies.json from {CSV_PATH.relative_to(ROOT)} "
        f"({len(rows)} companies, {len(category_groups(rows))} categories)"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ValueError as error:
        print(f"error: {error}", file=sys.stderr)
        raise SystemExit(1)
