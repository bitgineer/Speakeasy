.PHONY: help diagram diagram-png diagram-svg diagram-check

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
