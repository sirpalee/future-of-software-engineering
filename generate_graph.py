from __future__ import annotations

import argparse
import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parent
DEFAULT_INPUT = ROOT / "score.csv"
DEFAULT_OUTPUT = ROOT / "score_chart.png"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Plot score.csv as a PNG line chart using matplotlib."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_INPUT,
        help="Path to the score CSV file.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Path for the generated chart image.",
    )
    parser.add_argument(
        "--title",
        default="Daily Software Engineering score trend",
        help="Chart title.",
    )
    return parser.parse_args()


def read_score_csv(score_csv: Path) -> tuple[list[int], list[float]]:
    if not score_csv.exists():
        raise FileNotFoundError(f"Score file not found: {score_csv}")

    rows = []
    with score_csv.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise ValueError("Score CSV must have a header row")

        header_map = {name.lower(): name for name in reader.fieldnames}
        day_field = header_map.get("day")
        score_field = header_map.get("score")
        if day_field is None or score_field is None:
            raise ValueError("Score CSV needs columns named 'Day' and 'Score'")

        rows = list(reader)

    if not rows:
        raise ValueError("Score CSV is empty")

    days = [int(row[day_field]) for row in rows]
    scores = [float(row[score_field]) for row in rows]
    return days, scores


def make_png_chart(
    days: list[int], scores: list[float], title: str, output_path: Path
) -> Path:
    output_path = output_path.expanduser().resolve().with_suffix(".png")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    plt.style.use("seaborn-v0_8-whitegrid")
    fig, ax = plt.subplots(figsize=(12, 6.75), dpi=120)
    ax.plot(days, scores, color="#1f77b4", linewidth=2.5, marker="o", markersize=6)
    ax.set_title(title)
    ax.set_xlabel("Day")
    ax.set_ylabel("Score")
    ax.set_ylim(0, 100)
    ax.grid(True, linewidth=0.7, alpha=0.45)
    fig.tight_layout()
    fig.savefig(output_path, format="png")
    plt.close(fig)
    return output_path


def make_chart(input_csv: Path, output_path: Path, title: str) -> Path:
    days, scores = read_score_csv(input_csv)
    return make_png_chart(days, scores, title, output_path)


def main() -> None:
    args = parse_args()
    chart_path = make_chart(args.input, args.output, args.title)
    print(f"Wrote {chart_path}")


if __name__ == "__main__":
    main()
