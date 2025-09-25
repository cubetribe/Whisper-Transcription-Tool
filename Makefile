# Makefile for Whisper Transcription Tool Testing

.PHONY: help test test-unit test-integration test-performance test-all
.PHONY: coverage lint format security docs clean install dev-install
.PHONY: test-quick test-ci benchmark profile

# Default target
help:
	@echo "Available targets:"
	@echo "  test-quick     - Run quick unit tests"
	@echo "  test-unit      - Run all unit tests"
	@echo "  test-integration - Run integration tests"
	@echo "  test-performance - Run performance tests"
	@echo "  test-all       - Run all tests"
	@echo "  test-ci        - Run CI test suite"
	@echo "  coverage       - Generate test coverage report"
	@echo "  lint          - Run code linting"
	@echo "  format        - Format code with black and isort"
	@echo "  security      - Run security checks"
	@echo "  benchmark     - Run performance benchmarks"
	@echo "  profile       - Profile performance bottlenecks"
	@echo "  docs          - Generate documentation"
	@echo "  clean         - Clean build artifacts"
	@echo "  install       - Install package"
	@echo "  dev-install   - Install in development mode"

# Test targets
test-quick:
	@echo "Running quick unit tests..."
	pytest tests/unit -v --tb=short -x --durations=5

test-unit:
	@echo "Running unit tests..."
	pytest tests/unit -v --tb=short --durations=10

test-integration:
	@echo "Running integration tests..."
	pytest tests/integration -v --tb=short -m "not requires_model"

test-performance:
	@echo "Running performance tests..."
	pytest tests/performance -v --tb=short -m "not slow"

test-all:
	@echo "Running all tests..."
	pytest tests -v --tb=short --durations=10

test-ci:
	@echo "Running CI test suite..."
	pytest tests -v --tb=short --cov=src --cov-report=xml --cov-report=term-missing \
		--maxfail=5 --durations=10 -m "not (slow or requires_model)"

# Coverage
coverage:
	@echo "Generating test coverage report..."
	pytest tests -v --cov=src --cov-report=html --cov-report=xml --cov-report=term-missing
	@echo "Coverage report generated in htmlcov/index.html"

coverage-unit:
	@echo "Generating unit test coverage..."
	pytest tests/unit --cov=src --cov-report=html:htmlcov/unit --cov-report=term-missing

coverage-integration:
	@echo "Generating integration test coverage..."
	pytest tests/integration --cov=src --cov-report=html:htmlcov/integration --cov-report=term-missing

# Code quality
lint:
	@echo "Running code linting..."
	flake8 src tests
	black --check src tests
	isort --check-only src tests
	mypy src --ignore-missing-imports

format:
	@echo "Formatting code..."
	black src tests
	isort src tests
	@echo "Code formatted successfully!"

# Security
security:
	@echo "Running security checks..."
	safety check
	bandit -r src

# Performance
benchmark:
	@echo "Running performance benchmarks..."
	pytest tests/performance --benchmark-only --benchmark-sort=mean

profile:
	@echo "Profiling performance bottlenecks..."
	python -m cProfile -o profile_stats.prof -m pytest tests/performance -m "not slow"
	python -c "import pstats; p = pstats.Stats('profile_stats.prof'); p.sort_stats('cumtime').print_stats(20)"

# Memory analysis
memory-test:
	@echo "Running memory usage analysis..."
	pytest tests/performance::TestMemoryUsage -v --tb=short
	@echo "Memory test completed. Check output for memory usage patterns."

leak-test:
	@echo "Running memory leak detection..."
	pytest tests/performance::TestResourceLeakDetection -v --tb=short
	@echo "Leak detection completed."

# Stress testing
stress-test:
	@echo "Running stress tests..."
	pytest tests/performance::TestStressTests -v --tb=short -m slow
	@echo "Stress tests completed."

# Development
dev-install:
	@echo "Installing in development mode..."
	pip install -e ".[full,test]"
	@echo "Development installation complete!"

install:
	@echo "Installing package..."
	pip install .
	@echo "Installation complete!"

# Documentation
docs:
	@echo "Generating documentation..."
	sphinx-build -W -b html docs docs/_build/html
	@echo "Documentation generated in docs/_build/html/index.html"

# Cleanup
clean:
	@echo "Cleaning build artifacts..."
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf coverage.xml
	rm -rf .tox/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "profile_stats.prof" -delete
	@echo "Cleanup complete!"

clean-cache:
	@echo "Cleaning pytest and Python cache..."
	rm -rf .pytest_cache/
	rm -rf __pycache__/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@echo "Cache cleanup complete!"

# Test environment setup
test-env:
	@echo "Setting up test environment..."
	python -m venv test_venv
	./test_venv/bin/pip install -e ".[test]"
	@echo "Test environment ready in test_venv/"

# Test data generation
test-data:
	@echo "Generating test data..."
	python -c "
import tempfile
from pathlib import Path
temp_dir = Path('test_data')
temp_dir.mkdir(exist_ok=True)
(temp_dir / 'sample.txt').write_text('Das ist ein Test text mit fehler.')
(temp_dir / 'large.txt').write_text('Langer Test text. ' * 1000)
print('Test data generated in test_data/')
"

# Continuous testing
watch:
	@echo "Starting continuous testing (install pytest-watch first)..."
	ptw tests/ src/ --runner="pytest tests/unit -v --tb=short"

# Report generation
test-report:
	@echo "Generating comprehensive test report..."
	pytest tests --html=test-report.html --self-contained-html --cov=src --cov-report=html
	@echo "Test report generated: test-report.html and htmlcov/index.html"

# Performance comparison
perf-compare:
	@echo "Running performance comparison..."
	pytest tests/performance --benchmark-json=benchmark.json
	@echo "Benchmark results saved to benchmark.json"

# Test specific components
test-llm:
	pytest tests/unit/test_llm_corrector* -v

test-batch:
	pytest tests/unit/test_batch_processor* -v

test-resource:
	pytest tests/unit/test_resource_manager* -v

test-prompts:
	pytest tests/unit/test_correction_prompts* -v

test-api:
	pytest tests/integration/test_api* -v

test-workflow:
	pytest tests/integration/test_correction_workflow* -v

# GitHub Actions simulation
github-test:
	@echo "Simulating GitHub Actions test workflow..."
	$(MAKE) lint
	$(MAKE) test-ci
	$(MAKE) security
	@echo "GitHub Actions simulation complete!"

# Quality checks
quality:
	@echo "Running comprehensive quality checks..."
	$(MAKE) lint
	$(MAKE) security
	$(MAKE) test-unit
	$(MAKE) coverage
	@echo "Quality checks completed successfully!"