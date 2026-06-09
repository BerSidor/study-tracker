# Google Sheet Reference

## Web App

The sheet is kept up to date via a **Google Apps Script Web App** (`tracker.gs`).
The script is deployed from inside the Google Sheet and receives session data via HTTP POST.

After setup, the Web App URL and the Sheet URL are stored in `config.json`:
- `config.json` → `webAppUrl`  (used by PowerShell to POST session data)
- `config.json` → `sheetUrl`   (the human-readable link to share/bookmark)

For setup instructions see `SETUP.md`.

## Sheet Structure

**Section 1 (rows 1–20): Weekly Report**
- Week range, total hours, daily average, best day, peak time block
- Weekly goal progress bar
- Topic breakdown by track
- 3 recommended next topics with reasoning

**Section 2 (row 22+): Session Log**
Headers: `Date | Day | Start | End | Total Hrs | Topics (segments) | Notes`
Newest session first. Topics column format: `"Claude Code hooks (0.75h), MCP servers (1.17h)"`
