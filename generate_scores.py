from __future__ import annotations

import argparse
import csv
import re
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DEFAULT_OUTPUT = ROOT / "score.csv"

# Each report ends with:
#   Score
#   ```
#   <integer>
#   ```
# Line endings vary between reports (LF and CRLF), and the trailing newline is optional.
SCORE_PATTERN = re.compile(r"(?:^|\n)Score\r?\n```\r?\n\s*(\d+)\s*\r?\n```\s*\Z")


def find_reports(root: Path) -> dict[date, Path]:
    """Return every report file named after its ISO date, inside a year directory."""
    reports: dict[date, Path] = {}
    for candidate in root.glob("[0-9][0-9][0-9][0-9]/*"):
        if not candidate.is_file():
            continue
        try:
            report_date = date.fromisoformat(candidate.name)
        except ValueError:
            continue
        reports[report_date] = candidate
    return reports


def parse_report_score(report: Path) -> int:
    text = report.read_text(encoding="utf-8")
    match = SCORE_PATTERN.search(text)
    if not match:
        raise ValueError(f"{report}: no score found at the end of the report")
    score = int(match.group(1))
    if not 0 <= score <= 100:
        raise ValueError(f"{report}: score out of range 0-100: {score}")
    return score


def build_scores(root: Path) -> list[tuple[int, int]]:
    """Return (day, score) rows, where day 0 is the first recorded report."""
    reports = find_reports(root)
    if not reports:
        return []

    first_date = min(reports)
    rows: list[tuple[int, int]] = []
    errors: list[str] = []
    for report_date in sorted(reports):
        try:
            score = parse_report_score(reports[report_date])
        except ValueError as error:
            errors.append(str(error))
            continue
        rows.append(((report_date - first_date).days, score))

    if errors:
        raise ValueError("Could not read every report:\n" + "\n".join(errors))
    return rows


def write_scores_csv(rows: list[tuple[int, int]], output_path: Path) -> None:
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(["Day", "Score"])
        writer.writerows(rows)


def regenerate_scores(root: Path = ROOT, output_path: Path = DEFAULT_OUTPUT) -> int:
    rows = build_scores(root)
    write_scores_csv(rows, output_path)
    return len(rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Rebuild score.csv from the dated daily reports."
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Path for the generated CSV file.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    count = regenerate_scores(ROOT, args.output)
    print(f"Wrote {count} scores to {args.output}")


if __name__ == "__main__":
    main()
