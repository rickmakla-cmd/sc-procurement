# SC Procurement Tracker (Step 1)

This app checks South Carolina open solicitations and creates a CSV of **new** items since the last run.

Think of it like this:
- `baseline.csv` = your memory of what was already seen.
- `delta_latest.csv` = what is new today.

---

## 1) What this app does (plain language)

Every time you run it, it will:
1. Open the SC solicitation website.
2. Go through all pages of open solicitations.
3. Compare those results to your saved baseline list.
4. Create a "delta" CSV that only contains new solicitations.
5. Update the baseline so next run only shows new items.

---

## 2) Where files are stored

All paths below are inside this project folder: `/workspace/sc-procurement`

### Main files you care about
- **Latest delta (new items):**
  - `outputs/delta_latest.csv`
  - `output/delta_latest.csv` (same data, compatibility copy)
- **Timestamped delta history:**
  - `outputs/delta_YYYYMMDDTHHMMSSZ.csv`
  - `output/delta_YYYYMMDDTHHMMSSZ.csv`
- **Baseline file (memory of seen solicitations):**
  - `data/baseline.csv`

### Important note
- If there are **no new solicitations**, `delta_latest.csv` still exists, but it may only have the header row.

---

## 3) First-time setup (very simple)

Open terminal in Codex and run:

```bash
cd /workspace/sc-procurement
make build
```

What this does:
- Checks the script for syntax errors.
- It does **not** scrape yet.

---

## 4) Run the app (normal daily run)

### Easiest command

```bash
cd /workspace/sc-procurement
./run_codex.sh
```

You can also run:

```bash
cd /workspace/sc-procurement
python scraper.py
```

After run finishes, the terminal prints file locations, including:
- `Delta CSV: ...`
- `Latest Delta CSV: ...`
- `Compatibility Latest Delta CSV: ...`

---

## 5) How to get/download the CSV in Codex

After running, use either of these stable files:

- `/workspace/sc-procurement/outputs/delta_latest.csv`
- `/workspace/sc-procurement/output/delta_latest.csv`

If your tool only shows one folder name, check both `outputs/` and `output/`.

To confirm file exists, run:

```bash
cd /workspace/sc-procurement
ls -la outputs
ls -la output
```

---

## 6) Reset baseline (start over from empty)

Use this only when you intentionally want to "forget" all previous runs.

```bash
cd /workspace/sc-procurement
make reset
```

Equivalent command:

```bash
python scraper.py --reset-baseline
```

What reset means:
- `data/baseline.csv` is cleared (header only).
- On the next run, almost everything currently open will appear as "new".

---

## 7) Daily use checklist (copy/paste friendly)

1. Run:
   ```bash
   cd /workspace/sc-procurement
   ./run_codex.sh
   ```
2. Get file:
   - `/workspace/sc-procurement/outputs/delta_latest.csv`
   - or `/workspace/sc-procurement/output/delta_latest.csv`
3. Download/share that CSV.

---

## 8) What columns are in the delta CSV

The generated delta CSV contains:
- `Solicitation Number`
- `Solicitation Description`
- `Purchasing Agency`
- `Submission Ending Date/Time`
- `Link to Solicitation`

The link is the full real URL to the solicitation details page.

---

## 9) Troubleshooting

### "I do not see the file"
Run:

```bash
cd /workspace/sc-procurement
ls -la outputs
ls -la output
```

If missing, run scraper again:

```bash
./run_codex.sh
```

### "The file exists but has no rows"
That usually means there are no newly posted solicitations since your last run.

### "I want all open solicitations again"
Reset baseline, then run again:

```bash
make reset
./run_codex.sh
```

---

## 10) GitHub Actions automation (optional background)

This repo includes `.github/workflows/daily_procurement_delta.yml`.

It can:
- run daily at `11:15 UTC`,
- upload a delta artifact,
- and commit updated baseline changes.

For local Codex usage, you can ignore this and just use `./run_codex.sh`.
