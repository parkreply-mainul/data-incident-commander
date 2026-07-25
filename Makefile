.PHONY: check setup start seed test integration-test api frontend-setup frontend-test frontend-build frontend gate2-host-check remote-check remote-plan remote-deploy remote-verify remote-stop remote-clean smoke demo demo-check submission-check stop

VENV_DIR ?= .venv
API_HOST ?= 127.0.0.1
API_PORT ?= 8000
FRONTEND_PORT ?= 5173
REMOTE_ENV ?= deploy/env/remote.env.example

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

integration-test: setup
	@PYTHONPATH=src "$(VENV_DIR)/bin/python" -m pytest tests/integrations/datahub

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

gate2-host-check:
	@test -n "$(GATE2_EXPECTED_HOSTNAME)" || { \
		echo "ERROR: set GATE2_EXPECTED_HOSTNAME to the approved VM hostname." >&2; \
		exit 2; \
	}
	@bash deploy/scripts/check_gate2_base_host.sh \
		--expected-hostname "$(GATE2_EXPECTED_HOSTNAME)"

remote-check:
	@set -eu; \
	for script in deploy/scripts/*.sh; do \
		bash -n "$$script"; \
		bash "$$script" --help >/dev/null; \
	done; \
	bash tests/deploy/test_gitignore_policy.sh >/dev/null; \
	bash tests/deploy/test_docker_installer_preflight.sh >/dev/null 2>&1; \
	bash tests/deploy/test_docker_conflicts.sh >/dev/null 2>&1; \
	bash tests/deploy/test_verify_datahub_health.sh >/dev/null 2>&1; \
	bash tests/deploy/test_health_url_validation.sh >/dev/null 2>&1; \
	bash tests/deploy/test_gate2_base_host.sh >/dev/null 2>&1; \
	bash tests/deploy/test_remote_prerequisite_resources.sh >/dev/null 2>&1; \
	python3 -c 'compile(open("deploy/scripts/validate_health_urls.py", encoding="utf-8").read(), "deploy/scripts/validate_health_urls.py", "exec")'; \
	test -f deploy/nginx/data-incident-commander.conf.template; \
	rg -q 'location /api/' deploy/nginx/data-incident-commander.conf.template; \
	rg -q 'location \^~ /health' deploy/nginx/data-incident-commander.conf.template; \
	if rg -n '(PRIVATE KEY|AKIA[0-9A-Z]{16}|DATAHUB_GMS_TOKEN=.+)' deploy; then \
		echo "ERROR: deployment examples contain a secret-like value." >&2; \
		exit 1; \
	fi; \
	echo "Deployment artifacts passed local syntax and secret-placeholder checks."

remote-plan: remote-check
	@bash deploy/scripts/prepare_host.sh --env "$(REMOTE_ENV)" --plan
	@bash deploy/scripts/install_docker_ubuntu.sh --env "$(REMOTE_ENV)" --plan
	@bash deploy/scripts/deploy_datahub.sh --env "$(REMOTE_ENV)" --plan

remote-deploy:
	@bash deploy/scripts/deploy_datahub.sh --env "$(REMOTE_ENV)"

remote-verify:
	@bash deploy/scripts/verify_datahub.sh --env "$(REMOTE_ENV)"

remote-stop:
	@bash deploy/scripts/stop_datahub.sh --env "$(REMOTE_ENV)"

remote-clean:
	@bash deploy/scripts/cleanup_project_resources.sh --env "$(REMOTE_ENV)"

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
