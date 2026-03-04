# sc-procurement
Procurement processing app.

## Step 1: Daily solicitation delta tracking

This repository now includes a script that:

1. Queries the South Carolina solicitation search page (all open solicitations, up to 500).
2. Crawls all pagination pages.
3. Compares scraped records to a local baseline CSV.
4. Generates a delta CSV containing only new solicitations with columns:
   - Solicitation Number
   - Solicitation Description
   - Purchasing Agency
   - Submission Ending Date/Time
   - Link to Solicitation (full URL)
5. Updates baseline CSV for the next run.

## Usage

Run normal daily process:

```bash
python scraper.py
```

Reset baseline back to empty:

```bash
python scraper.py --reset-baseline
```

Outputs:

- Delta file: `outputs/delta_<UTC timestamp>.csv`
- Baseline file: `data/baseline.csv`

## GitHub Actions daily run

A workflow is included at `.github/workflows/daily_procurement_delta.yml`.

- Scheduled daily at **11:15 UTC**.
- Also supports manual trigger via **workflow_dispatch**.
- Uploads the generated delta CSV as an artifact named `procurement-delta`.
- Commits updated `data/baseline.csv` back to the branch.

In ChatGPT/Codex terminal runs, use the printed absolute `Delta CSV` path to download directly from the environment.


## Build and run

```bash
make build
make run
```
