# python -m venv .venv && source .venv/bin/activate
# run source .venv/bin/activate in multiple terminals to run more than 1 svc local
# pip install -r requirements.txt

# make core      # → http://localhost:8080/docs

.PHONY: core api install

install:
	pip install -r requirements.txt

core:
	PYTHONPATH=services/core uvicorn app.main:app --reload --port 8080
