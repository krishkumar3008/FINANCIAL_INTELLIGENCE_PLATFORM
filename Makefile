.PHONY: load ratios test report dashboard api clean

# Default shell for Windows compatibility if running in bash-like environments
SHELL := bash

# Python virtual environment paths
PYTHON := ./venv/Scripts/python
PIP := ./venv/Scripts/pip
PYTEST := ./venv/Scripts/pytest
STREAMLIT := ./venv/Scripts/streamlit
UVICORN := ./venv/Scripts/uvicorn

load:
	$(PYTHON) src/etl/loader.py

ratios:
	$(PYTHON) src/ratios.py

test:
	$(PYTEST) tests/

report:
	$(PYTHON) -c "import os; print('Report generated: check output/load_audit.csv and output/validation_failures.csv')"

dashboard:
	$(STREAMLIT) run src/dashboard.py

api:
	$(UVICORN) src.api:app --reload --host 127.0.0.1 --port 8000

clean:
	@powershell -Command "if (Test-Path nifty100.db) { Remove-Item nifty100.db -Force }"
	@powershell -Command "Get-ChildItem -Recurse -Filter __pycache__ | Remove-Item -Recurse -Force"
	@powershell -Command "Get-ChildItem -Recurse -Filter *.pyc | Remove-Item -Force"
	@powershell -Command "if (Test-Path output/load_audit.csv) { Remove-Item output/load_audit.csv -Force }"
	@powershell -Command "if (Test-Path output/validation_failures.csv) { Remove-Item output/validation_failures.csv -Force }"
