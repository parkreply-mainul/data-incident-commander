.PHONY: check setup start seed test smoke demo demo-check submission-check stop

VENV_DIR ?= .venv

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
	@PYTHONPATH=src "$(VENV_DIR)/bin/python" -m pytest tests/unit

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
