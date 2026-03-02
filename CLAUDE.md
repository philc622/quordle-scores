# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

Personal analytics project that collects Quordle game results from sent emails, stores them in SQLite, exports to CSV, and visualizes via a static GitHub Pages dashboard.

## Common commands

```bash
# Setup (create venv, install deps)
python -m venv .venv && source .venv/bin/activate  # or .\.venv\Scripts\Activate.ps1 on Windows
pip install -r requirements.txt

# Fetch Quordle emails → write to DB (prompts for credentials, or use env vars)
python email-reader-with-sqlite.py quordle_scores.db
# Env vars: IMAP_SERVER, EMAIL_USERNAME, EMAIL_PASSWORD

# Export DB → CSV for dashboard
python extract_to_csv.py quordle_scores.db quordle-data/quordle_scores.csv

# Bulk import from CSV → DB (defaults to import.csv and quordle_scores.db)
python insert_from_csv.py

# Preview dashboard (serve repo root so /docs/ and /quordle-data/ share same origin)
python -m http.server 8000
# Open http://localhost:8000/docs/index.html
```

## Architecture & data flow

```
Quordle result emails (IMAP Sent folder)
  → email-reader-with-sqlite.py  (parse emoji scores → quordle_scores.db)
  → extract_to_csv.py            (SQLite → quordle-data/quordle_scores.csv)
  → docs/index.html              (client-side Chart.js dashboard, reads /quordle-data/quordle_scores.csv)
```

GitHub Actions (`.github/workflows/static.yml`) deploys `docs/` to GitHub Pages on push to main.

`update_score.sh` is a bash orchestration script (intended for Linux/WSL) that runs the full pipeline and pushes to GitHub.

## Database schema

Table `quordle_scores` in `quordle_scores.db`:
- `email_date` TEXT, `parsed_date` TEXT (ISO YYYY-MM-DD)
- `score1..score4` INTEGER — numeric score per puzzle (1–12) or **13 for a fail** (red square emoji → 13)
- `raw_email` TEXT, `date_added` TIMESTAMP

## Key conventions & gotchas

- **Fail encoding:** Red square emoji (🟥) maps to `13`. Do not change `parseSnippet` in `email-reader-with-sqlite.py` or the dashboard filters will break.
- **CSV format is canonical:** Header must be `Date,Score 1,Score 2,Score 3,Score 4,Sum,Max`. The dashboard (`docs/index.html`) depends on this exact header.
- **Missed days:** Rows with `Sum === 52` (four fails) are filtered out in the dashboard.
- **Deduplication:** Both `email-reader-with-sqlite.py` and `insert_from_csv.py` check for existing rows before inserting.
- **Schema changes:** If you modify the DB schema, update both the `CREATE TABLE` DDL in `email-reader-with-sqlite.py` and the queries in `extract_to_csv.py`.
- **`insert_from_csv.py`** has hardcoded input filename (`import.csv`) — adjust in the script if needed.
- **Dashboard data source:** `docs/index.html` fetches `/quordle-data/quordle_scores.csv` at runtime; the `quordle-data/` directory must be served at the same root as `docs/`.
