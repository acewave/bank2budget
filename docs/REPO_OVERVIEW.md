## What this is
A small toolset (CLI + browser UI) that converts bank-exported CSV files into YNAB/Actual Budget import CSVs — aimed at personal use to batch-convert exports from Butterfield Bank, Wise, Revolut, etc.

### Stack
- **Language(s):** Python (primary), JavaScript (browser UI), Shell (scripts / .bat wrappers)
- **Framework / runtime:** Plain Python scripts (CLI), static web frontend (HTML + JS) — intended for static hosting (Cloudflare Pages / wrangler)
- **Notable libraries:** pandas (used by tests/converters for tabular transforms), Cloudflare Pages / wrangler (deployment), Python standard libraries for CSV/date/decimal handling, unittest (test suite)

## How it's organized
```
.AGENTS/               agent metadata (repo-specific agent guidance)
.vscode/               editor settings
AGENTS.md              agent/triage notes
README.md              project overview (CLI)
README-WEB.md          web UI usage & deployment
index.html             browser UI (static)
style.css              web UI styling
converter.js           client-side CSV -> YNAB converter (browser)
assets/                static assets (icons/images)
bin/                   helper CLI/orchestrator (bin/unify-convert.py)
bob-to-actual.py       Python converter for Butterfield Bank (bob)
revolut-to-actual.py   Python converter for Revolut
wise-to-actual.py      Python converter for Wise
test_converters.py     unittest suite (uses pandas, exercises converters)
wrangler.toml          Cloudflare Pages configuration / deployment metadata
*.bat                  Windows helpers to run specific converters
```

How it fits together:
- The repo provides per-source Python converters (bob, revolut, wise) that parse bank CSVs and emit YNAB-compatible CSV files named with account and date-range. A small orchestrator (bin/unify-convert.py) detects the source file type and delegates to the right converter. In parallel, there is a browser-based port (index.html + converter.js) that reproduces the bob converter entirely client-side so users can convert files in their browser without uploading data. Tests (test_converters.py) validate conversion logic (the tests exercise pandas-based transforms and the headless conversion flow).

## How to run it
Web UI (quickest): open index.html in any modern browser and upload CSV files; processing happens client-side.
CLI (conversion of files in a directory):
- Place bank CSV(s) in the same directory as the script and run the appropriate converter, for example:
  - python bob-to-actual.py
  - python revolut-to-actual.py
  - python wise-to-actual.py
Or use the orchestrator:
  - python bin/unify-convert.py <input-file-or-directory>

Run tests (requires pandas):
- pip install pandas
- python -m unittest test_converters.py

Deploy web UI to Cloudflare Pages (as shown in README-WEB.md):
- npm install -g @cloudflare/wrangler
- wrangler login
- wrangler pages deploy . --project-name ynab-bob
Note: wrangler.toml contains placeholders for production route/zone_id — supply your Cloudflare zone/route for a real production deploy.

## Try asking
- Can you add a requirements.txt or pyproject.toml listing runtime deps (e.g., pandas) so the CLI and tests install cleanly?
- Do you want the orchestrator (bin/unify-convert.py) wired up as an installable CLI entrypoint (console_script) so users can run `unify-convert` directly?
- Are the sample CSVs referenced by tests (./.scratch/*.csv) current — would you like me to add a small sample dataset or CI job that runs test_converters.py automatically?
