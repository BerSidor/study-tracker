# Study Tracker — One-Time Setup

## Step 1 — Create the Google Sheet

1. Go to https://sheets.google.com
2. Click **Blank** to create a new spreadsheet
3. Rename it **"Study Tracker 2026"** (click the title at the top)
4. Copy the URL from your browser and save it — you'll need it in Step 4

## Step 2 — Add the Apps Script

1. In the sheet, click **Extensions > Apps Script**
2. Delete all existing code in the editor
3. Open `C:\Users\berna\study-tracker\tracker.gs` in any text editor
4. Copy everything and paste it into the Apps Script editor
5. Click **Save** (the floppy disk icon or Ctrl+S)
6. Name the project **"Study Tracker"** if prompted

## Step 3 — Deploy the Web App

1. Click **Deploy > New deployment**
2. Click the gear icon next to "Select type" and choose **Web app**
3. Set:
   - Description: `Study Tracker API`
   - Execute as: **Me**
   - Who has access: **Anyone**
4. Click **Deploy**
5. Click **Authorize access** and approve the permissions
6. **Copy the Web App URL** — it looks like:
   `https://script.google.com/macros/s/XXXXXXXXXX/exec`

## Step 4 — Save the URLs

Tell Claude Code:

> The Apps Script URL is https://script.google.com/macros/s/XXXXXXXXXX/exec
> The sheet URL is https://docs.google.com/spreadsheets/d/XXXXXXXXXX/edit

Claude Code will save both into `config.json` automatically.

---

## That's it. You're ready to track.

From now on, just say things like:
- **"start studying Claude Code hooks"** — begins a session
- **"switching to MCP servers"** — switches topic mid-session
- **"done"** — closes the session and updates the sheet
- **"weekly report"** — triggers a report refresh and gives you the sheet link
