# Use bash with strict options
SHELL := /usr/bin/env bash
.SHELLFLAGS := -eu -o pipefail -c

# Avoid inheriting any existing virtual environment
unexport VIRTUAL_ENV

# Default target when running plain `make`
.DEFAULT_GOAL := help

.PHONY: help init_workspace run test uninstall_pre_commit remove_caches clean_workspace lint fmt typecheck pre-commit

help:
	@echo "Available targets:"
	@echo "  init_workspace    - set up venv, install deps, install pre-commit hooks"
	@echo "  run               - run the main application"
	@echo "  test              - run the test suite"
	@echo "  uninstall_pre_commit - uninstall pre-commit git hooks"
	@echo "  remove_caches     - remove ruff, mypy, and pre-commit caches"
	@echo "  clean_workspace   - remove hooks, caches, and .venv"
	@echo "  lint              - run ruff (lint)"
	@echo "  fmt               - run ruff formatter"
	@echo "  typecheck         - run mypy"
	@echo "  pre-commit        - run all pre-commit hooks on all files"

init_workspace:
	@echo ">>> Checking for uv..."
	@command -v uv >/dev/null 2>&1 || { \
		echo "ERROR: 'uv' is not installed."; \
		echo "Install instructions: https://docs.astral.sh/uv/getting-started/installation/"; \
		exit 1; \
	}
	@echo ">>> Syncing environment with uv (creating .venv if needed)..."
	uv sync --extra dev
	@echo ">>> Installing pre-commit git hooks..."
	uv run pre-commit install
	@echo ">>> Workspace initialized. You're ready to develop."

run:
	@PYTHONPATH=src uv run python -m banking_rest_service.main

test:
	uv run pytest

uninstall_pre_commit:
	@echo ">>> Uninstalling pre-commit git hooks..."
	uv run pre-commit uninstall || true
	@echo ">>> Pre-commit hooks uninstalled."

remove_caches:
	@echo ">>> Removing ruff cache..."
	rm -rf .ruff_cache || true
	@echo ">>> Removing mypy cache..."
	rm -rf .mypy_cache || true
	@echo ">>> Removing pre-commit cache..."
	uv run pre-commit clean	|| true
	@echo ">>> Caches removed."

clean_workspace: uninstall_pre_commit remove_caches
	@echo ">>> Removing virtual environment..."
	rm -rf .venv || true
	@echo ">>> Workspace cleaned."

lint:
	uv run ruff check .

fmt:
	uv run ruff format .

typecheck:
	uv run mypy src

pre-commit:
	uv run pre-commit run --all-files
