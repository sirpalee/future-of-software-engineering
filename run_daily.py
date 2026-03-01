from __future__ import annotations

from datetime import date
from pathlib import Path
import csv
import os
import re

from openai import OpenAI


ROOT = Path(__file__).resolve().parent
README_PATH = ROOT / "README.md"
SCORE_CSV_PATH = ROOT / "score.csv"
API_KEY_PATH = ROOT / "OPENAI.key"
RESEARCH_REQUIREMENTS = "\n\n".join(
    [
        "Additional requirements:",
        "- Use web sources when helpful.",
        "- Include references as markdown links at the end.",
        "- Cite only broadly credible/public sources.",
    ]
)


def extract_prompt(readme: str, heading: str) -> str:
    pattern = rf"{re.escape(heading)}\n```\n(.*?)\n```"
    match = re.search(pattern, readme, flags=re.DOTALL)
    if not match:
        raise ValueError(f"Could not find prompt block for heading: {heading}")
    return match.group(1).strip()


def parse_score(text: str) -> int:
    match = re.search(r"\d+", text)
    if not match:
        raise ValueError(f"Model did not return an integer score. Got: {text!r}")
    score = int(match.group(0))
    if score < 0 or score > 100:
        raise ValueError(f"Score out of range 0-100: {score}")
    return score


def next_day_index(score_csv_path: Path) -> int:
    if not score_csv_path.exists():
        return 0

    with score_csv_path.open("r", newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))

    if not rows:
        return 0

    return int(rows[-1]["Day"]) + 1


def first_recorded_analysis_date(root: Path) -> date | None:
    dated_files: list[date] = []
    for candidate in root.glob("*/*"):
        if not candidate.is_file():
            continue
        try:
            dated_files.append(date.fromisoformat(candidate.name))
        except ValueError:
            continue

    if not dated_files:
        return None
    return min(dated_files)


def day_index_for_date(today: date, root: Path, score_csv_path: Path) -> int:
    first_date = first_recorded_analysis_date(root)
    if first_date is None:
        return next_day_index(score_csv_path)
    return (today - first_date).days


def append_score(day: int, score: int, score_csv_path: Path) -> None:
    file_exists = score_csv_path.exists()
    needs_newline = False

    if file_exists and score_csv_path.stat().st_size > 0:
        with score_csv_path.open("rb") as check_handle:
            check_handle.seek(-1, 2)
            needs_newline = check_handle.read(1) != b"\n"

    with score_csv_path.open("a", newline="", encoding="utf-8") as handle:
        if needs_newline:
            handle.write("\n")
        writer = csv.writer(handle)
        if not file_exists:
            writer.writerow(["Day", "Score"])
        writer.writerow([day, score])


def write_daily_file(target_path: Path, analysis: str, score: int) -> None:
    content = "\n".join(
        [
            "Analysis",
            "```",
            analysis,
            "```",
            "Score",
            "```",
            str(score),
            "```",
            "",
        ]
    )
    target_path.write_text(content, encoding="utf-8")


def main() -> None:
    readme_text = README_PATH.read_text(encoding="utf-8")
    research_prompt = extract_prompt(readme_text, "Research prompt:")
    scoring_prompt = extract_prompt(readme_text, "Scoring prompt:")

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key and API_KEY_PATH.exists():
        api_key = API_KEY_PATH.read_text(encoding="utf-8").strip()
    if not api_key:
        raise ValueError("Missing API key. Set OPENAI_API_KEY or add it to OPENAI.key")

    client = OpenAI(api_key=api_key)

    analysis_response = client.responses.create(
        model="gpt-5-pro",
        reasoning={"effort": "high"},
        tools=[{"type": "web_search_preview"}],
        input=f"{research_prompt}\n\n{RESEARCH_REQUIREMENTS}",
    )
    analysis_text = analysis_response.output_text.strip()

    score_response = client.responses.create(
        model="gpt-5-pro",
        previous_response_id=analysis_response.id,
        input=scoring_prompt,
    )
    score = parse_score(score_response.output_text.strip())

    today = date.today()
    year_dir = ROOT / str(today.year)
    year_dir.mkdir(parents=True, exist_ok=True)
    daily_file_path = year_dir / today.isoformat()

    write_daily_file(daily_file_path, analysis_text, score)

    day = day_index_for_date(today, ROOT, SCORE_CSV_PATH)
    append_score(day, score, SCORE_CSV_PATH)

    print(f"Wrote analysis to {daily_file_path}")
    print(f"Appended score {score} at Day {day} in {SCORE_CSV_PATH}")


if __name__ == "__main__":
    main()
