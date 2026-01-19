# Repository Guidelines

## Project Structure & Module Organization
- `run_newsletter.py` orchestrates the pipeline and writes dated `ai_weekly_YYYYMMDD.html` plus Bluesky thread files to the repo root.
- `newsletter_generator.py` fans out to RSS (`rss_scraper.py`), Reddit (`reddit_scraper.py`), trends (`trend_analyzer.py`), summaries (`summarizer.py`), and Bluesky copy (`bluesky_generator.py`).
- Keep helpers and configuration constants next to the feature module they serve; introduce `tests/` when adding pytest coverage.

## Build, Test, and Development Commands
- `python -m venv venv && source venv/bin/activate` prepares an isolated dev shell; leave `venv/` untracked.
- `pip install -r requirements.txt` syncs scraping, NLP, and templating deps after dependency changes.
- `export ANTHROPIC_API_KEY="..."` unlocks Claude summaries; otherwise run `python run_newsletter.py --no-ai`.
- `python run_newsletter.py --days 7` is the end-to-end smoke; append `--help` for filters, output locations, and rate knobs.
- `python rss_scraper.py` or `python reddit_scraper.py` lets you debug feed parsing without running the full generator.

## Coding Style & Naming Conventions
- Follow PEP 8: four-space indentation, snake_case for functions and globals, PascalCase only for classes like `NewsletterGenerator`.
- Prefer single-purpose functions with docstrings when logic is opaque; reuse the concise emoji logging already present.
- Store prompt templates, source lists, and weight tables beside the consuming module to avoid brittle imports.

## Testing Guidelines
- No automated suite yet; manually run the relevant script and review generated HTML/JSON artifacts before merging.
- When adding non-trivial logic, stub `tests/test_<feature>.py` with `pytest` and document manual verification steps in the PR body.

## Commit & Pull Request Guidelines
- Use Conventional Commits such as `feat: tune trend scoring` or `fix: guard empty rss feeds` to keep history searchable.
- Keep commits scoped to one concern and call out new env vars, services, or artifact names in the body.
- Pull requests need a short summary, artifact paths for review, manual test notes, and linked issues or TODOs.

## Security & Configuration Tips
- Load secrets from environment variables or a local `.env` ignored by git; never hard-code tokens.
- Respect existing throttling when adding network calls, and flag new rate-limit considerations in docs or PR notes.
