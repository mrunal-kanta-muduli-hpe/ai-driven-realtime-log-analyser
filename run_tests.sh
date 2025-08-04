#!/bin/bash

# Test Runner Script for Smart Log Analyzer
# This script runs different types of tests and generates reports

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check dependencies
check_dependencies() {
    print_status "Checking dependencies..."
    
    if ! command_exists python3; then
        print_error "Python 3 is not installed"
        exit 1
    fi
    
    if ! command_exists pip3; then
        print_error "pip3 is not installed"
        exit 1
    fi
    
    # Check if virtual environment exists
    if [[ ! -d "venv" ]]; then
        print_warning "Virtual environment not found. Creating one..."
        python3 -m venv venv
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Install test dependencies
    print_status "Installing test dependencies..."
    pip install -r requirements.txt
    pip install pytest pytest-cov pytest-mock pytest-html
}

# Run unit tests
run_unit_tests() {
    print_status "Running unit tests..."
    
    python -m pytest tests/unit/ \
        -v \
        --tb=short \
        --cov=src \
        --cov-report=term-missing \
        --cov-report=html:reports/coverage \
        --html=reports/unit_tests.html \
        --self-contained-html \
        -m "not slow"
    
    if [[ $? -eq 0 ]]; then
        print_success "Unit tests passed!"
    else
        print_error "Unit tests failed!"
        return 1
    fi
}

# Run integration tests
run_integration_tests() {
    print_status "Running integration tests..."
    
    python -m pytest tests/integration/ \
        -v \
        --tb=short \
        --html=reports/integration_tests.html \
        --self-contained-html \
        -m "not jira"  # Skip Jira tests by default
    
    if [[ $? -eq 0 ]]; then
        print_success "Integration tests passed!"
    else
        print_error "Integration tests failed!"
        return 1
    fi
}

# Run Jira integration tests (optional)
run_jira_tests() {
    print_status "Running Jira integration tests..."
    print_warning "These tests require valid Jira credentials in config/config.yaml"
    
    read -p "Do you want to run Jira tests? [y/N]: " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        python -m pytest tests/integration/ \
            -v \
            --tb=short \
            -m "jira"
        
        if [[ $? -eq 0 ]]; then
            print_success "Jira tests passed!"
        else
            print_error "Jira tests failed!"
            return 1
        fi
    else
        print_status "Skipping Jira tests"
    fi
}

# Run performance tests
run_performance_tests() {
    print_status "Running performance tests..."
    
    python -m pytest tests/integration/ \
        -v \
        --tb=short \
        -m "slow" \
        --html=reports/performance_tests.html \
        --self-contained-html
    
    if [[ $? -eq 0 ]]; then
        print_success "Performance tests passed!"
    else
        print_error "Performance tests failed!"
        return 1
    fi
}

# Run linting and code quality checks
run_code_quality() {
    print_status "Running code quality checks..."
    
    # Install linting tools if not present
    pip install flake8 black isort mypy
    
    # Run black for code formatting check
    print_status "Checking code formatting with black..."
    black --check --diff src/ tests/
    
    # Run isort for import sorting check
    print_status "Checking import sorting with isort..."
    isort --check-only --diff src/ tests/
    
    # Run flake8 for linting
    print_status "Running flake8 linting..."
    flake8 src/ tests/ --max-line-length=88 --extend-ignore=E203,W503
    
    # Run mypy for type checking (optional)
    if command_exists mypy; then
        print_status "Running mypy type checking..."
        mypy src/ --ignore-missing-imports || print_warning "Type checking completed with warnings"
    fi
    
    print_success "Code quality checks completed!"
}

# Generate test reports
generate_reports() {
    print_status "Generating test reports..."
    
    # Create reports directory
    mkdir -p reports
    
    # Generate coverage report
    if [[ -d "htmlcov" ]]; then
        cp -r htmlcov reports/coverage
        print_success "Coverage report available at reports/coverage/index.html"
    fi
    
    # Generate test summary
    cat > reports/test_summary.md << EOF
# Test Summary Report

Generated on: $(date)

## Test Results

### Unit Tests
- Location: tests/unit/
- Report: unit_tests.html

### Integration Tests  
- Location: tests/integration/
- Report: integration_tests.html

### Coverage Report
- Location: reports/coverage/index.html

## Running Tests

\`\`\`bash
# Run all tests
./run_tests.sh

# Run specific test types
./run_tests.sh unit
./run_tests.sh integration
./run_tests.sh performance
./run_tests.sh quality

# Run with coverage
./run_tests.sh coverage
\`\`\`

## Test Structure

- **Unit Tests**: Test individual components in isolation
- **Integration Tests**: Test component interactions and workflows
- **Performance Tests**: Test scalability and performance
- **Jira Tests**: Test Jira API integration (requires credentials)

EOF
    
    print_success "Test summary generated at reports/test_summary.md"
}

# Main execution logic
main() {
    print_status "Smart Log Analyzer Test Runner"
    print_status "=============================="
    
    # Create reports directory
    mkdir -p reports
    
    # Parse command line arguments
    case "${1:-all}" in
        "unit")
            check_dependencies
            run_unit_tests
            ;;
        "integration")
            check_dependencies
            run_integration_tests
            ;;
        "jira")
            check_dependencies
            run_jira_tests
            ;;
        "performance")
            check_dependencies
            run_performance_tests
            ;;
        "quality")
            check_dependencies
            run_code_quality
            ;;
        "coverage")
            check_dependencies
            run_unit_tests
            run_integration_tests
            ;;
        "all"|*)
            check_dependencies
            run_unit_tests
            run_integration_tests
            run_performance_tests
            run_code_quality
            run_jira_tests
            generate_reports
            ;;
    esac
    
    print_success "Test execution completed!"
    print_status "Check the reports/ directory for detailed results"
}

# Help function
show_help() {
    cat << EOF
Smart Log Analyzer Test Runner

Usage: $0 [COMMAND]

Commands:
    all          Run all tests and generate reports (default)
    unit         Run unit tests only
    integration  Run integration tests only
    jira         Run Jira integration tests only
    performance  Run performance tests only
    quality      Run code quality checks only
    coverage     Run unit and integration tests with coverage
    help         Show this help message

Examples:
    $0                 # Run all tests
    $0 unit           # Run only unit tests
    $0 coverage       # Run tests with coverage report
    $0 quality        # Run code quality checks

EOF
}

# Handle help
if [[ "${1}" == "help" ]] || [[ "${1}" == "-h" ]] || [[ "${1}" == "--help" ]]; then
    show_help
    exit 0
fi

# Run main function
main "$@"
