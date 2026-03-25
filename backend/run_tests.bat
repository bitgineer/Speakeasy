@echo off
REM Windows Test Runner for Speakeasy Backend
REM Usage: run_tests.bat [options]
REM 
REM Options:
REM   hotspot     - Run only hotspot tests (critical path)
REM   integration - Run integration tests
REM   all         - Run all tests (default)
REM   coverage    - Run with coverage report
REM   clean       - Clean test artifacts
REM   help        - Show this help message

setlocal enabledelayedexpansion

REM Configuration
set BACKEND_DIR=%~dp0
set VENV_DIR=%BACKEND_DIR%\.venv
set PYTHON_CMD=uv run

REM Parse arguments
set TEST_PATTERN=
set WITH_COVERAGE=

if "%1"=="" goto run_all
if "%1"=="help" goto show_help
if "%1"=="hotspot" set TEST_PATTERN=tests/test_hotspot_*.py
if "%1"=="integration" set TEST_PATTERN=tests/ -m integration
if "%1"=="all" set TEST_PATTERN=tests/
if "%1"=="clean" goto clean
if "%1"=="coverage" set WITH_COVERAGE=--cov=speakeasy --cov-report=html --cov-report=term

:run_all
if "%TEST_PATTERN%"=="" set TEST_PATTERN=tests/

echo.
echo ============================================
echo    Speakeasy Backend Test Runner
echo ============================================
echo.
echo Running tests: %TEST_PATTERN%
echo Working directory: %BACKEND_DIR%
echo.

cd /d %BACKEND_DIR%

REM Check if .venv exists, if not sync dependencies
if not exist "%VENV_DIR%" (
    echo Setting up virtual environment...
    uv sync --all-extras --dev
    if errorlevel 1 (
        echo.
        echo ERROR: Failed to setup virtual environment
        echo Run: uv sync --all-extras --dev
        exit /b 1
    )
)

REM Run tests
echo.
echo Running tests...
echo.

if "%WITH_COVERAGE%"=="" (
    %PYTHON_CMD% pytest %TEST_PATTERN% -v
) else (
    %PYTHON_CMD% pytest %TEST_PATTERN% -v %WITH_COVERAGE%
)

set TEST_RESULT=%errorlevel%

echo.
echo ============================================
if %TEST_RESULT%==0 (
    echo    ✓ All tests passed!
) else (
    echo    ✗ Some tests failed (exit code: %TEST_RESULT%)
)
echo ============================================
echo.

if exist "%BACKEND_DIR%\htmlcov\index.html" (
    echo Coverage report generated: %BACKEND_DIR%\htmlcov\index.html
    echo Open with: start htmlcov\index.html
    echo.
)

exit /b %TEST_RESULT%


:clean
echo.
echo Cleaning test artifacts...
echo.
cd /d %BACKEND_DIR%

if exist ".pytest_cache" rmdir /s /q .pytest_cache
if exist "__pycache__" rmdir /s /q __pycache__
if exist "htmlcov" rmdir /s /q htmlcov
if exist ".coverage" del /q .coverage
if exist "coverage.xml" del /q coverage.xml

for /d /r . %%d in (__pycache__) do @if exist "%%d" rmdir /s /q "%%d"

echo Clean complete!
echo.
exit /b 0


:show_help
echo.
echo Speakeasy Backend Test Runner
echo =============================
echo.
echo Usage: run_tests.bat [option]
echo.
echo Options:
echo   hotspot     Run only hotspot tests (critical path - 75, 24, 22, 21 caller functions)
echo   integration Run integration tests (multi-step flows)
echo   all         Run all tests (default)
echo   coverage    Run with HTML coverage report
echo   clean       Clean test artifacts (.pytest_cache, __pycache__, htmlcov)
echo   help        Show this help message
echo.
echo Examples:
echo   run_tests.bat              - Run all tests
echo   run_tests.bat hotspot      - Run critical hotspot tests only
echo   run_tests.bat coverage     - Run all tests with coverage
echo   run_tests.bat clean        - Clean test artifacts
echo.
echo Prerequisites:
echo   - UV package manager installed
echo   - Python 3.11+ available
echo   - Dependencies installed via: uv sync --all-extras --dev
echo.
echo Test Categories:
echo   - Hotspot Tests: Critical functions with many callers (cleanup, add, request, etc.)
echo   - Integration Tests: Multi-step execution flows
echo   - Unit Tests: Individual function tests
echo   - E2E Tests: End-to-end workflow tests (in gui/e2e/)
echo.
exit /b 0
