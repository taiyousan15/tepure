#!/bin/bash
# Backend test runner script

set -e  # Exit on error

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Backend Test Runner ===${NC}\n"

# Check if we're in backend directory
if [ ! -f "app.py" ]; then
    echo -e "${RED}Error: Please run this script from the backend directory${NC}"
    exit 1
fi

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo -e "${YELLOW}pytest not found. Installing development dependencies...${NC}"
    pip3 install -r requirements-dev.txt || {
        echo -e "${RED}Failed to install dependencies${NC}"
        exit 1
    }
fi

# Parse command line arguments
TEST_PATH="${1:-tests}"
COVERAGE_REPORT="${2:-term-missing}"

echo -e "${GREEN}Running tests from: ${TEST_PATH}${NC}"
echo -e "${GREEN}Coverage report: ${COVERAGE_REPORT}${NC}\n"

# Run tests with coverage
pytest "${TEST_PATH}" \
    --cov=. \
    --cov-report="${COVERAGE_REPORT}" \
    --cov-config=.coveragerc \
    -v \
    -ra \
    --tb=short

# Check exit code
if [ $? -eq 0 ]; then
    echo -e "\n${GREEN}✅ All tests passed!${NC}"
else
    echo -e "\n${RED}❌ Some tests failed${NC}"
    exit 1
fi
