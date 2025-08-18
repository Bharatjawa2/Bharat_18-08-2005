.PHONY: install run trigger get report db-status clean

# Default target: set up a virtualenv and install dependencies
install:
	@if [ ! -d .venv ]; then \
		python3 -m venv .venv; \
	fi
	@. .venv/bin/activate && pip install --upgrade pip && pip install -r requirements.txt

# Run the FastAPI server
run:
	@. .venv/bin/activate && uvicorn app.main:app --host 0.0.0.0 --port 8000

# Trigger a report and print the returned report_id
trigger:
	@curl -s -X POST http://localhost:8000/trigger_report | python3 -c 'import sys, json; print(json.load(sys.stdin)["report_id"])'

# Get report by report_id (usage: make get REPORT_ID=<uuid>)
get:
	@if [ -z "$(REPORT_ID)" ]; then \
		echo "Usage: make get REPORT_ID=<uuid>"; exit 1; \
	fi
	@curl -L http://localhost:8000/get_report/$(REPORT_ID) -o reports/$(REPORT_ID).csv
	@echo "Saved to reports/$(REPORT_ID).csv"

# Quick DB status of latest reports
db-status:
	@sqlite3 data.db 'SELECT report_id, status, csv_path FROM reports ORDER BY created_at DESC LIMIT 10;'

clean:
	rm -f data.db
	rm -rf reports/*.csv
	rm -rf .venv

