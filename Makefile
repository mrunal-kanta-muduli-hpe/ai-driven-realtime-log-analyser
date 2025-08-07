# Makefile for AI Driven Realtime Log Analyser

.PHONY: help install test clean demo serve realtime-dashboard lint format

# Default target
help:
	@echo "AI Driven Realtime Log Analyser - Development Commands"
	@echo "=================================================="
	@echo ""
	@echo "Available commands:"
	@echo "  install           - Install dependencies"
	@echo "  test              - Run all tests"
	@echo "  demo              - Run complete demo"
	@echo "  clean             - Clean generated files"
	@echo "  serve             - Start static dashboard server"
	@echo "  realtime-dashboard - Start real-time dashboard"
	@echo "  lint              - Run code linting"
	@echo "  format            - Format code"
	@echo "  analyze           - Run basic log analysis"
	@echo "  build             - Build package"
	@echo ""

# Install dependencies
install:
	pip install -r requirements.txt

# Install in development mode
install-dev:
	pip install -e .
	pip install -r requirements.txt

# Run tests
test:
	pytest tests/ -v --cov=src --cov-report=html

# Run demo
demo:
	./demo.sh

# Clean generated files
clean:
	rm -rf analysis-results/
	rm -rf test-results/
	rm -rf __pycache__/
	rm -rf src/__pycache__/
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf *.egg-info/
	find . -name "*.pyc" -delete
	find . -name "*.pyo" -delete

# Basic analysis
analyze:
	python main.py --debug

# Start static dashboard server
serve:
	python main.py --serve --port 8889

# Start real-time dashboard
realtime-dashboard:
	python main.py --realtime-dashboard --port 8889

# Real-time monitoring only
realtime:
	python main.py --realtime --debug

# Code linting
lint:
	@echo "Running flake8..."
	@flake8 src/ main.py || echo "flake8 not installed, skipping"
	@echo "Running pylint..."
	@pylint src/ main.py || echo "pylint not installed, skipping"

# Code formatting
format:
	@echo "Running black..."
	@black src/ main.py || echo "black not installed, skipping"
	@echo "Running isort..."
	@isort src/ main.py || echo "isort not installed, skipping"

# Build package
build:
	python setup.py sdist bdist_wheel

# Show project status
status:
	@echo "Project Structure:"
	@tree -I '__pycache__|*.pyc|analysis-results|test-results' || ls -la
	@echo ""
	@echo "Git Status:"
	@git status || echo "Not a git repository"

# Quick test with sample data
quick-test:
	python main.py --log-file sample-data/valogs.log --output-dir test-results --debug

# Generate documentation
docs:
	@echo "Generating documentation..."
	@echo "Main README.md is the primary documentation"
	@echo "Demo script: ./demo.sh"
	@echo "Usage: python main.py --help"

# Docker build (if Dockerfile exists)
docker-build:
	@if [ -f Dockerfile ]; then \
		docker build -t ai-log-analyser .; \
	else \
		echo "Dockerfile not found"; \
	fi

# Docker run
docker-run:
	docker run -p 8889:8889 -p 8890:8890 ai-log-analyser

# Check dependencies
check-deps:
	pip check

# Upgrade dependencies
upgrade-deps:
	pip list --outdated

# Security check
security-check:
	@safety check || echo "safety not installed, run: pip install safety"

# Full quality check
quality: lint test
	@echo "Quality check completed"

# Setup development environment
setup-dev: install-dev
	@echo "Development environment setup completed"
	@echo "Run 'make demo' to test the installation"
