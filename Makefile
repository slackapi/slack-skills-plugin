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

OLLAMA_DIR := .ollama
OLLAMA_BIN := $(OLLAMA_DIR)/bin/ollama
OLLAMA_MODELS := $(OLLAMA_DIR)/models
OLLAMA_MODEL := $(or $(OLLAMA_MODEL_NAME),gemma4)

UNAME_S := $(shell uname -s)

TARGETS := help install install-test install-tools clean lint format test test-unit test-eval cursor-install cursor-uninstall

.PHONY: $(TARGETS)

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

$(VENV):
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip

$(OLLAMA_BIN):
	mkdir -p $(OLLAMA_DIR)/bin $(OLLAMA_MODELS)
ifeq ($(UNAME_S),Darwin)
	curl -fSL "https://github.com/ollama/ollama/releases/latest/download/ollama-darwin.tgz" | tar xz -C $(OLLAMA_DIR)/bin
else
	curl -fSL "https://github.com/ollama/ollama/releases/latest/download/ollama-linux-amd64.tar.zst" | zstd -d | tar x -C $(OLLAMA_DIR) --strip-components=0
endif
	chmod +x $(OLLAMA_BIN)

install: install-test install-tools $(OLLAMA_BIN) ## Set up everything (venv + deps + Ollama)
	@OLLAMA_PID=""; \
	if ! OLLAMA_MODELS=$(OLLAMA_MODELS) $(OLLAMA_BIN) list > /dev/null 2>&1; then \
		echo "Starting Ollama server..."; \
		OLLAMA_MODELS=$(OLLAMA_MODELS) $(OLLAMA_BIN) serve > /dev/null 2>&1 & \
		OLLAMA_PID=$$!; \
		for i in $$(seq 1 30); do \
			curl -sf http://localhost:11434/api/version > /dev/null 2>&1 && break; \
			sleep 1; \
		done; \
	fi; \
	OLLAMA_MODELS=$(OLLAMA_MODELS) $(OLLAMA_BIN) pull $(OLLAMA_MODEL); \
	$(DEEPEVAL) set-ollama --model=$(OLLAMA_MODEL); \
	if [ -n "$$OLLAMA_PID" ]; then \
		echo "Stopping Ollama server (PID $$OLLAMA_PID)..."; \
		kill $$OLLAMA_PID 2>/dev/null; \
	fi

install-test: $(VENV) ## Install test dependencies (deepeval)
	$(PIP) install --upgrade pip
	$(PIP) install -e ".[test]"

install-tools: $(VENV) ## Install linting/formatting tools (ruff)
	$(PIP) install --upgrade pip
	$(PIP) install -e ".[tools]"

clean: ## Remove virtual environment, Ollama, and local Cursor install
	-$(PYTHON) scripts/cursor.py uninstall
	rm -rf $(VENV) $(OLLAMA_DIR)

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

test-eval: ## Run LLM-judged tests (requires Ollama; set testdir=<path> to target specific files)
	@OLLAMA_PID=""; \
	if ! OLLAMA_MODELS=$(OLLAMA_MODELS) $(OLLAMA_BIN) list > /dev/null 2>&1; then \
		echo "Starting Ollama server..."; \
		OLLAMA_MODELS=$(OLLAMA_MODELS) $(OLLAMA_BIN) serve > /dev/null 2>&1 & \
		OLLAMA_PID=$$!; \
		for i in $$(seq 1 30); do \
			curl -sf http://localhost:11434/api/version > /dev/null 2>&1 && break; \
			sleep 1; \
		done; \
	fi; \
	$(DEEPEVAL) test run $(or $(testdir),tests/eval/) -v; \
	TEST_EXIT=$$?; \
	if [ -n "$$OLLAMA_PID" ]; then \
		echo "Stopping Ollama server (PID $$OLLAMA_PID)..."; \
		kill $$OLLAMA_PID 2>/dev/null; \
	fi; \
	exit $$TEST_EXIT
