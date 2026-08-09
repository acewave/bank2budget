# Import Automation Ideas — bank2budget

This file captures high-level ideas for combining the existing per-source converters (bob, wise, revolut) into a single, efficient system for producing files ready to import into Actual Budget. Keep iterating and refining here.

## Goals
- Reduce manual steps when converting exports for Actual Budget
- Make conversion predictable, testable, and automatable
- Maintain easy review when desired (preview mode)

## High-level approaches
- Unified CLI orchestrator (Recommended first step)
  - Single command that auto-detects source CSV and dispatches the matching converter plugin.
  - Outputs per-account Actual/YNAB CSVs in an output folder (or in-place).
  - Supports headless (batch) and interactive (preview) modes.

- Watch / Inbox folder + batch mode
  - Drop raw exports into a watched directory; a daemon or scheduled job processes new files.
  - Write converted files to an output folder and optionally flag processed files.

- Simple GUI or local web UI
  - Preview transformations, map accounts, resolve ambiguous detections, and trigger conversion and import.
  - Implement as a small Flask app (local) or Tauri desktop app for native feel.

- OS-specific automation for Actual
  - macOS: AppleScript/Automator to drive Actual's import UI and confirm account selection.
  - Windows: UI Automation / PowerShell scripts (higher maintenance).

- Cloud connectors (future)
  - Fetch statements via provider APIs (requires auth, security model). Useful if you want continuous automated ingest.

## Language & packaging trade-offs
- Python (Recommended)
  - Fast iteration, existing codebase, wide library support (csv, pandas), easy tests and CI.
  - Can produce installers / single-file bundles (PyInstaller) for non-dev users.

- Go / Rust / Node
  - Single static binaries and easier distribution; better for performance or stricter deployment constraints.

## Architecture suggestions
- Plugin per source (bob/wise/revolut)
  - Expose detect(input_path) -> bool, and transform(input_path) -> standardized rows + metadata.
  - Keep converters small and testable.

- Standardized internal model
  - Define a canonical row format (Date, Payee, Memo, Outflow, Inflow, AccountID, SourceFile).

- Config + mappings
  - Per-user config for account mappings, output folder, thresholds (currency-detect), and behavior (auto-import or manual).

- Robustness
  - Explicit errors (no bare excepts), logging, and CI tests for malformed inputs.
  - Dry-run/preview mode and atomic output (write to temp then move).

## Next steps (suggested roadmap)
1. Implement unified CLI that chooses converter by inspecting file headers/content.
2. Define and document plugin interface; refactor existing scripts to match it.
3. Add unit tests for the orchestrator and detection logic (edge cases: mixed currencies, empty files).
4. Add optional watch mode and a simple preview UI (web or TUI).
5. Consider packaging (PyInstaller) for distribution.

## Open questions
- Do you want automatic import into Actual (requires UI automation) or prefer manual import after conversion?
- Minimum detection confidence threshold before auto-mapping account.


Feel free to edit and expand this file as the design converges.