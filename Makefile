# python -m venv .venv && source .venv/bin/activate
# run source .venv/bin/activate in multiple terminals to run more than 1 svc local
# pip install -r requirements.txt

# make core      # → http://localhost:8080/docs

# Setup:
#   python3.11 -m venv .venv && source .venv/bin/activate
#   make install
#
# Local dev:
#   make core                     -> http://localhost:8080/docs
#   make hosts                    one-time: add hostname to /etc/hosts (sudo)
#   make proxy                    Caddy -> https://api.local.<APP_NAME>.com
#   make run SVC=ingest PORT=8081 a second service later

ROOT     := $(patsubst %/,%,$(dir $(realpath $(firstword $(MAKEFILE_LIST)))))
PY       := $(ROOT)/.venv/bin
APP_NAME ?= template
SVC      ?= core
PORT     ?= 8080

.PHONY: install lock run core proxy hosts unhosts check-venv

check-venv:
	@test -x $(PY)/python || { echo "No venv at $(ROOT)/.venv -- run: python3.11 -m venv .venv"; exit 1; }

install: check-venv
	$(PY)/python -m pip install -r $(ROOT)/requirements.txt --require-hashes

lock:
	cd $(ROOT) && uv pip compile requirements.in -o requirements.txt --generate-hashes

run: check-venv
	cd $(ROOT) && \
	  PYTHONPATH=$(ROOT)/deployables/$(SVC) \
	  PYTHONDONTWRITEBYTECODE=1 \
	  ENV=local APP_NAME=$(APP_NAME) \
	  $(PY)/uvicorn app.main:app --reload \
	    --reload-dir $(ROOT)/deployables/$(SVC) \
	    --reload-dir $(ROOT)/shared \
	    --port $(PORT)

core:
	$(MAKE) run SVC=core PORT=8080

proxy:
	cd $(ROOT) && caddy run --config Caddyfile

hosts:
	@grep -q "api.local.$(APP_NAME).com" /etc/hosts \
	  || echo "127.0.0.1 api.local.$(APP_NAME).com" | sudo tee -a /etc/hosts
	@echo "-> https://api.local.$(APP_NAME).com/docs"

unhosts:
	@sudo sed -i '' "/api.local.$(APP_NAME).com/d" /etc/hosts