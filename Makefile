# CodeRefinery Makefile
.PHONY: help install install-dev test test-cov lint format clean docs run-example run-web

help: ## Show this help message
	@echo "CodeRefinery Development Commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install the package in development mode
	pip install -e .

install-dev: ## Install with development dependencies
	pip install -e ".[dev,tools]"

test: ## Run tests
	pytest

test-cov: ## Run tests with coverage
	pytest --cov=coderefinery --cov-report=html --cov-report=term-missing

lint: ## Run linting tools
	@echo "Running flake8..."
	flake8 coderefinery tests examples
	@echo "Running mypy..."
	mypy coderefinery
	@echo "Linting complete!"

format: ## Format code with black
	black coderefinery tests examples

clean: ## Clean up build artifacts
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf htmlcov/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

docs: ## Generate documentation (placeholder)
	@echo "Documentation generation not yet implemented"

run-example: ## Run the example analysis
	python examples/example_analysis.py

run-web: ## Launch the web interface
	streamlit run coderefinery/web_app.py

check: lint test ## Run all checks (lint + test)

setup-hooks: ## Setup git hooks (placeholder)
	@echo "Git hooks setup not yet implemented"

dist: clean ## Build distribution packages
	python -m build

upload: dist ## Upload to PyPI (placeholder)
	@echo "PyPI upload not yet configured"