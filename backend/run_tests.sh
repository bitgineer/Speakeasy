#!/bin/bash
# macOS/Linux Test Runner for Speakeasy Backend
# Usage: ./run_tests.sh [options]

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR"
VENV_DIR="$BACKEND_DIR/.venv"
PYTHON_CMD="uv run"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Parse arguments
TEST_PATTERN=""
WITH_COVERAGE=""

show_help() {
    echo ""
    echo "Speakeasy Backend Test Runner"
    echo "=============================="
    echo ""
    echo "Usage: ./run_tests.sh [option]"
    echo ""
    echo "Options:"
    echo "  hotspot     Run only hotspot tests (critical path - 75, 24, 22, 21 caller functions)"
    echo "  integration Run integration tests (multi-step flows)"
    echo "  all         Run all tests (default)"
    echo "  coverage    Run with HTML coverage report"
    echo "  clean       Clean test artifacts (.pytest_cache, __pycache__, htmlcov)"
    echo "  help        Show this help message"
    echo ""
    echo "Examples:"
    echo "  ./run_tests.sh              - Run all tests"
    echo "  ./run_tests.sh hotspot      - Run critical hotspot tests only"
    echo "  ./run_tests.sh coverage     - Run all tests with coverage"
    echo "  ./run_tests.sh clean        - Clean test artifacts"
    echo ""
}

clean_artifacts() {
    echo ""
    echo "Cleaning test artifacts..."
    cd "$BACKEND_DIR"
    
    rm -rf .pytest_cache __pycache__ htmlcov .coverage coverage.xml
    find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
    
    echo -e "${GREEN}Clean complete!${NC}"
    echo ""
    exit 0
}

run_tests() {
    echo ""
    echo -e "${YELLOW}============================================${NC}"
    echo -e "${YELLOW}   Speakeasy Backend Test Runner${NC}"
    echo -e "${YELLOW}============================================${NC}"
    echo ""
    echo "Running tests: ${TEST_PATTERN:-tests/}"
    echo "Working directory: $BACKEND_DIR"
    echo ""
    
    cd "$BACKEND_DIR"
    
    # Check if .venv exists, if not sync dependencies
    if [ ! -d "$VENV_DIR" ]; then
        echo -e "${YELLOW}Setting up virtual environment...${NC}"
        uv sync --all-extras --dev
        if [ $? -ne 0 ]; then
            echo -e "${RED}ERROR: Failed to setup virtual environment${NC}"
            echo "Run: uv sync --all-extras --dev"
            exit 1
        fi
    fi
    
    # Run tests
    echo ""
    echo -e "${YELLOW}Running tests...${NC}"
    echo ""
    
    if [ -z "$WITH_COVERAGE" ]; then
        $PYTHON_CMD pytest ${TEST_PATTERN:-tests/} -v
    else
        $PYTHON_CMD pytest ${TEST_PATTERN:-tests/} -v $WITH_COVERAGE
    fi
    
    TEST_RESULT=$?
    
    echo ""
    echo -e "${YELLOW}============================================${NC}"
    if [ $TEST_RESULT -eq 0 ]; then
        echo -e "${GREEN}   ✓ All tests passed!${NC}"
    else
        echo -e "${RED}   ✗ Some tests failed (exit code: $TEST_RESULT)${NC}"
    fi
    echo -e "${YELLOW}============================================${NC}"
    echo ""
    
    if [ -f "$BACKEND_DIR/htmlcov/index.html" ]; then
        echo -e "${GREEN}Coverage report generated: $BACKEND_DIR/htmlcov/index.html${NC}"
        echo "Open with: open htmlcov/index.html (macOS) or xdg-open htmlcov/index.html (Linux)"
        echo ""
    fi
    
    exit $TEST_RESULT
}

# Main logic
case "${1:-}" in
    hotspot)
        TEST_PATTERN="tests/test_hotspot_*.py"
        run_tests
        ;;
    integration)
        TEST_PATTERN="tests/ -m integration"
        run_tests
        ;;
    all)
        TEST_PATTERN="tests/"
        run_tests
        ;;
    coverage)
        WITH_COVERAGE="--cov=speakeasy --cov-report=html --cov-report=term"
        TEST_PATTERN="tests/"
        run_tests
        ;;
    clean)
        clean_artifacts
        ;;
    help|--help|-h)
        show_help
        exit 0
        ;;
    "")
        TEST_PATTERN="tests/"
        run_tests
        ;;
    *)
        echo -e "${RED}Unknown option: $1${NC}"
        echo ""
        show_help
        exit 1
        ;;
esac
