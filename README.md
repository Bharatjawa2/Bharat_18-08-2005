## Store Monitoring API

FastAPI backend that ingests the provided CSVs into SQLite and exposes two endpoints to generate and fetch uptime/downtime reports per store computed within business hours.

### Requirements

- Python 3.10+
- macOS/Linux (Windows via WSL works)

### Quick start (Makefile)

```bash
make
make run
```

This will create `.venv/`, install dependencies, and start the API at `http://0.0.0.0:8000`.

Trigger and download a report:

```bash
REPORT_ID=$(make -s trigger)
echo $REPORT_ID
make get REPORT_ID=$REPORT_ID
```

Check report statuses:

```bash
make db-status
```

### Run locally (manual)

1. Install deps:
   
   ```bash
   pip install -r requirements.txt
   ```

2. Start server:
   
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```

On first start, the app loads CSVs from `data/` into `data.db`:

- `data/store_status.csv` → `polls`
- `data/menu_hours.csv` → `business_hours`
- `data/timezones.csv` → `timezones`

### API

- `POST /trigger_report` → `{ "report_id": "..." }`
  - Queues report generation and returns an ID immediately.

- `GET /get_report/{report_id}`
  - Returns `Running` while processing.
  - Returns the CSV file when `Complete`.
  - Optional: `GET /get_report/{report_id}?statusOnly=true` returns only status: `Running`, `Complete`, or `Failed: ...`.

CSV schema:

`store_id, uptime_last_hour(in minutes), uptime_last_day(in hours), update_last_week(in hours), downtime_last_hour(in minutes), downtime_last_day(in hours), downtime_last_week(in hours)`

Notes:

- Uptime/downtime are computed only within business hours (defaults to 24x7 if missing).
- Timestamps from polls are treated as UTC and compared against business hours converted from store local time using the store timezone (defaults to `America/Chicago` if missing).
- Interpolation uses midpoints between consecutive polls to assign continuous status over time.

### Makefile targets

- `make` (or `make install`): create virtualenv and install dependencies
- `make run`: start the API
- `make trigger`: trigger a report and print the `report_id`
- `make get REPORT_ID=<uuid>`: download CSV to `reports/<uuid>.csv`
- `make db-status`: show last 10 report rows from SQLite
- `make clean`: remove `.venv`, `data.db`, and generated CSVs

### Push to GitHub

```bash
git init
git add .
git commit -m "Store monitoring backend: API, DB ingestion, reporting, Makefile, docs"
git branch -M main
git remote add origin <your_repo_git_url>
git push -u origin main
```


