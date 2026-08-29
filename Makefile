# python -m venv .venv && source .venv/bin/activate
# run source .venv/bin/activate in multiple terminals to run more than 1 svc local
# pip install -r requirements.txt

# make core      # → http://localhost:8080/docs
# make markets   # → http://localhost:8081/docs
# make worker    # runs the Kalshi sync once

.PHONY: core markets worker install

install:
	pip install -r requirements.txt

core:
	PYTHONPATH=services/core uvicorn app.main:app --reload --port 8080

markets:
	PYTHONPATH=services/markets uvicorn app.main:app --reload --port 8081

worker:
	PYTHONPATH=services/markets python -m app.worker