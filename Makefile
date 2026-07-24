.PHONY: check setup start seed test api frontend-setup frontend-test frontend-build frontend smoke demo demo-check submission-check stop

VENV_DIR ?= .venv
API_HOST ?= 127.0.0.1
API_PORT ?= 8000
FRONTEND_PORT ?= 5173

check:
	@./scripts/check_prerequisites.sh

setup:
	@set -eu; \
	if [ ! -x "$(VENV_DIR)/bin/python" ]; then \
		python_cmd=""; \
		for candidate in python3.11 python3; do \
			if command -v "$$candidate" >/dev/null 2>&1 && \
				"$$candidate" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)'; then \
				python_cmd="$$candidate"; \
				break; \
			fi; \
		done; \
		if [ -z "$$python_cmd" ]; then \
			echo "ERROR: Python 3.11 or newer is required to create $(VENV_DIR)." >&2; \
			exit 1; \
		fi; \
		echo "Creating repository-local virtual environment at $(VENV_DIR) with $$python_cmd."; \
		"$$python_cmd" -m venv "$(VENV_DIR)"; \
	fi; \
	"$(VENV_DIR)/bin/python" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)' || { \
		echo "ERROR: $(VENV_DIR) does not use Python 3.11 or newer; remove it explicitly and rerun make setup." >&2; \
		exit 1; \
	}; \
	echo "Installing pinned repository dependencies into $(VENV_DIR)."; \
	"$(VENV_DIR)/bin/python" -m pip install --disable-pip-version-check -r requirements-backend.txt

start:
	@echo "Placeholder: start is not implemented yet."

seed:
	@echo "Placeholder: seed is not implemented yet."

test: setup
	@PYTHONPATH=src "$(VENV_DIR)/bin/python" -m pytest

api: setup
	@PYTHONPATH=src DIC_HOST="$(API_HOST)" DIC_PORT="$(API_PORT)" \
		"$(VENV_DIR)/bin/python" -m uvicorn data_incident_commander.api.app:app \
		--host "$(API_HOST)" --port "$(API_PORT)"

frontend-setup:
	@npm --prefix frontend ci

frontend-test: frontend-setup
	@npm --prefix frontend test

frontend-build: frontend-setup
	@npm --prefix frontend run build

frontend: frontend-setup
	@npm --prefix frontend run dev -- --host 127.0.0.1 --port "$(FRONTEND_PORT)"

smoke:
	@echo "Placeholder: smoke is not implemented yet."

demo:
	@echo "Placeholder: demo is not implemented yet."

demo-check:
	@echo "Placeholder: demo-check is not implemented yet."

submission-check:
	@echo "Placeholder: submission-check is not implemented yet."

stop:
	@echo "Placeholder: stop is not implemented yet."
