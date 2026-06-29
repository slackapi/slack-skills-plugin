VENV := .venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip
RUFF := $(VENV)/bin/ruff
DEEPEVAL := $(VENV)/bin/deepeval

# Load .env if present (see .env.example) and export its vars to recipe
# subprocesses. The leading `-` no-ops when .env is absent; bare `export` only
# exports *defined* vars, so a missing .env never shadows the in-code defaults.
-include .env
export

TARGETS := help install install-test install-tools clean lint format test test-unit test-eval cursor-install cursor-uninstall

.PHONY: $(TARGETS)

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

$(VENV):
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip

install: install-test install-tools ## Set up everything (venv + deps)

install-test: $(VENV) ## Install test dependencies (deepeval)
	$(PIP) install --upgrade pip
	$(PIP) install -e ".[test]"

install-tools: $(VENV) ## Install linting/formatting tools (ruff)
	$(PIP) install --upgrade pip
	$(PIP) install -e ".[tools]"

clean: ## Remove virtual environment and local Cursor install
	-$(PYTHON) scripts/cursor.py uninstall
	rm -rf $(VENV)

cursor-install: $(VENV) ## Install this plugin into a local Cursor for development
	$(PYTHON) scripts/cursor.py install

cursor-uninstall: $(VENV) ## Uninstall this plugin from the local Cursor install
	$(PYTHON) scripts/cursor.py uninstall

lint: ## Run ruff linter checks
	$(RUFF) check .

format: ## Auto-format code with ruff
	$(RUFF) format .
	$(RUFF) check --fix .

test: ## Run all tests (set testdir=<path> to route to the matching runner)
ifdef testdir
	@if echo "$(testdir)" | grep -q "tests/eval"; then \
		$(MAKE) test-eval testdir="$(testdir)"; \
	else \
		$(MAKE) test-unit testdir="$(testdir)"; \
	fi
else
	@$(MAKE) test-unit
	@$(MAKE) test-eval
endif

test-unit: ## Run structural/unit validation tests (set testdir=<path> to target specific files)
	$(PYTHON) -m pytest $(or $(testdir),tests/unit/) -v

test-eval: ## Run LLM-judged tests (requires GEMINI_API_KEY; set testdir=<path> to target specific files)
	$(DEEPEVAL) test run $(or $(testdir),tests/eval/) -v
