# NodeAI Backend Testing Makefile
.PHONY: test test-unit test-integration test-fast test-slow test-all test-coverage clean-test install-test-deps

# Python and test runner
PYTHON := python
PYTEST := $(PYTHON) -m pytest
TEST_RUNNER := $(PYTHON) run_tests.py

# Test commands
test: test-fast
	@echo "✅ Fast tests completed"

test-unit:
	@echo "🧪 Running unit tests..."
	$(TEST_RUNNER) --suite unit

test-integration:
	@echo "🔗 Running integration tests..."
	$(TEST_RUNNER) --suite integration

test-fast:
	@echo "⚡ Running fast tests..."
	$(TEST_RUNNER) --suite fast

test-slow:
	@echo "🐌 Running slow tests..."
	$(TEST_RUNNER) --suite slow

test-all:
	@echo "🎯 Running all tests..."
	$(TEST_RUNNER) --suite all

test-coverage:
	@echo "📊 Running tests with coverage..."
	$(TEST_RUNNER) --suite all --coverage

test-parallel:
	@echo "⚡ Running tests in parallel..."
	$(TEST_RUNNER) --suite fast --parallel auto

test-verbose:
	@echo "🔍 Running tests with verbose output..."
	$(TEST_RUNNER) --suite fast --verbose

# Specific test patterns
test-retry:
	@echo "🔄 Running retry logic tests..."
	$(TEST_RUNNER) --pattern "retry"

test-rate-limit:
	@echo "⏱️  Running rate limiting tests..."
	$(TEST_RUNNER) --pattern "rate" --verbose

test-chat:
	@echo "💬 Running chat node tests..."
	$(TEST_RUNNER) --pattern "chat"

test-api:
	@echo "🌐 Running API tests..."
	$(TEST_RUNNER) --file tests/integration/test_api_health_and_core.py

# Test maintenance
install-test-deps:
	@echo "📦 Installing test dependencies..."
	pip install -r test_requirements.txt

clean-test:
	@echo "🧹 Cleaning test artifacts..."
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf coverage.xml
	rm -rf .pytest_cache/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Development helpers
test-watch:
	@echo "👀 Watching for changes and running tests..."
	$(PYTHON) -m pytest --looponfail tests/

lint-tests:
	@echo "🔍 Linting test files..."
	flake8 tests/ --count --select=E9,F63,F7,F82 --show-source --statistics

# CI/CD helpers
ci-test:
	@echo "🤖 Running CI test suite..."
	$(TEST_RUNNER) --suite all --coverage --parallel auto

# Help
help:
	@echo "NodeAI Backend Test Commands:"
	@echo ""
	@echo "Basic Testing:"
	@echo "  test           - Run fast tests (default)"
	@echo "  test-unit      - Run only unit tests"
	@echo "  test-integration - Run only integration tests"
	@echo "  test-fast      - Run fast tests (excludes slow tests)"
	@echo "  test-slow      - Run only slow tests"
	@echo "  test-all       - Run all tests"
	@echo ""
	@echo "Coverage & Performance:"
	@echo "  test-coverage  - Run all tests with coverage report"
	@echo "  test-parallel  - Run tests in parallel"
	@echo "  test-verbose   - Run tests with verbose output"
	@echo ""
	@echo "Specific Test Types:"
	@echo "  test-retry     - Run retry logic tests"
	@echo "  test-rate-limit - Run rate limiting tests"
	@echo "  test-chat      - Run chat node tests"
	@echo "  test-api       - Run API endpoint tests"
	@echo ""
	@echo "Maintenance:"
	@echo "  install-test-deps - Install test dependencies"
	@echo "  clean-test     - Clean test artifacts"
	@echo "  lint-tests     - Lint test files"
	@echo "  ci-test        - Full CI test suite"