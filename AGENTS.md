# Agent guidelines

These rules apply to any AI coding agent working in this repository.

## Git workflow
- Commit and push directly to `main`. Do not create branches.
- Author and commit as `Pal Mezei <sirpalee@users.noreply.github.com>`.
- Do not add agent or tool attribution to commit messages, such as `Co-Authored-By`, session links or "Generated with" lines.

## Data files
- The daily reports in `<year>/<YYYY-MM-DD>` are the source of truth. Each one ends with a `Score` block containing a single integer.
- `score.csv` and `score_chart.png` are generated. Do not edit them by hand. CI rebuilds both on every push with `generate_scores.py` and `generate_graph.py`.
- Day numbers are the number of days since the first report (2026-02-08).
