.PHONY: help diagram diagram-png diagram-svg diagram-check
.PHONY: build build-flet build-qt build-portable build-installer
.PHONY: test clean clean-all release

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-20s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

## Dependency Diagram
diagram: ## Generate/update dependency diagram (DOT format)
	python3 scripts/generate_dependency_diagram.py -o docs/dependencies.dot

diagram-png: diagram ## Generate dependency diagram as PNG
	python3 scripts/generate_dependency_diagram.py -o docs/dependencies.png -f png

diagram-svg: diagram ## Generate dependency diagram as SVG
	python3 scripts/generate_dependency_diagram.py -o docs/dependencies.svg -f svg

diagram-check: ## Check if dependency diagram is up to date
	@python3 scripts/generate_dependency_diagram.py --summary-only
	@echo "Run 'make diagram' to update the diagram"

## Build and Release
build: ## Build full Windows distribution (installer + portable)
	python scripts/build.py

build-flet: ## Build Flet GUI version (default)
	python scripts/build.py --spec flet

build-qt: ## Build Qt GUI version
	python scripts/build.py --spec qt

build-portable: ## Build only portable ZIP
	python scripts/build.py --no-installer

build-installer: ## Build only NSIS installer
	python scripts/build.py --no-portable

build-no-tests: ## Build without running tests
	python scripts/build.py --skip-tests

test: ## Run test suite
	python scripts/build.py --test-only

clean: ## Clean build artifacts
	python scripts/build.py --clean-only

clean-all: ## Clean all build artifacts and cache
	python scripts/build.py --clean-only
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true

release: ## Create a full release (clean, test, build all)
	python scripts/build.py
