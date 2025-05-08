#!/bin/bash

# Videntify Testing Helper Script
# This script makes it easy to run different types of tests for the Videntify project

# Set colors for prettier output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Display usage information
usage() {
  echo -e "${BLUE}Videntify Testing Helper${NC}"
  echo -e "Usage: $0 [OPTIONS] [COMPONENT_NAME]"
  echo -e ""
  echo -e "Options:"
  echo -e "  ${GREEN}ui${NC}           Run all UI tests"
  echo -e "  ${GREEN}ui-coverage${NC}  Run UI tests with coverage report"
  echo -e "  ${GREEN}ui-watch${NC}     Run UI tests in watch mode"
  echo -e "  ${GREEN}ui-component${NC} Run tests for a specific component (provide component name as arg)"
  echo -e "  ${GREEN}backend${NC}      Run all backend tests"
  echo -e "  ${GREEN}all${NC}          Run both UI and backend tests"
  echo -e "  ${GREEN}ci${NC}           Run all tests in CI mode (no watch, with coverage)"
  echo -e "  ${GREEN}help${NC}         Display this help message"
  echo -e ""
  echo -e "Examples:"
  echo -e "  $0 ui-component Login     # Test the Login component"
  echo -e "  $0 ui-coverage           # Run all UI tests with coverage"
  echo -e "  $0 all                   # Run all tests"
}

# Function to run UI tests
run_ui_tests() {
  echo -e "\n${BLUE}Running UI tests...${NC}\n"
  cd "$(dirname "$0")/ui" || { echo -e "${RED}Error: UI directory not found${NC}"; exit 1; }
  npm test -- --watchAll=false
}

# Function to run UI tests with coverage
run_ui_coverage() {
  echo -e "\n${BLUE}Running UI tests with coverage...${NC}\n"
  cd "$(dirname "$0")/ui" || { echo -e "${RED}Error: UI directory not found${NC}"; exit 1; }
  npm run test:coverage
}

# Function to run UI tests in watch mode
run_ui_watch() {
  echo -e "\n${BLUE}Running UI tests in watch mode...${NC}\n"
  cd "$(dirname "$0")/ui" || { echo -e "${RED}Error: UI directory not found${NC}"; exit 1; }
  npm test
}

# Function to run tests for a specific component
run_ui_component() {
  if [ -z "$1" ]; then
    echo -e "${RED}Error: Component name required${NC}"
    usage
    exit 1
  fi
  
  echo -e "\n${BLUE}Running tests for component: $1${NC}\n"
  cd "$(dirname "$0")/ui" || { echo -e "${RED}Error: UI directory not found${NC}"; exit 1; }
  npm test -- -t "$1"
}

# Function to run backend tests
run_backend_tests() {
  echo -e "\n${BLUE}Running backend tests...${NC}\n"
  cd "$(dirname "$0")" || { echo -e "${RED}Error: Root directory not found${NC}"; exit 1; }
  python -m pytest
}

# Function to run all tests
run_all_tests() {
  run_ui_tests
  run_backend_tests
}

# Function to run all tests in CI mode
run_ci_tests() {
  echo -e "\n${BLUE}Running all tests in CI mode...${NC}\n"
  
  # Run UI tests with CI configuration
  echo -e "\n${YELLOW}Running UI Tests (CI mode)...${NC}"
  cd "$(dirname "$0")/ui" || { echo -e "${RED}Error: UI directory not found${NC}"; exit 1; }
  npm run test:ci
  UI_EXIT=$?
  
  # Run backend tests
  echo -e "\n${YELLOW}Running Backend Tests...${NC}"
  cd "$(dirname "$0")" || { echo -e "${RED}Error: Project root directory not found${NC}"; exit 1; }
  python -m pytest --cov=src/ --cov-report=xml
  BACKEND_EXIT=$?
  
  # Show a helpful message about CI/CD integration
  echo -e "\n${GREEN}CI Tests Complete${NC}"
  echo -e "These are the same tests that will run in the GitHub Actions CI/CD pipeline."
  echo -e "If they pass locally, they should pass in CI as well."
  
  # Return non-zero if either test suite failed
  [ $UI_EXIT -ne 0 ] || [ $BACKEND_EXIT -ne 0 ] && exit 1
  exit 0
}

# Main script execution
case "$1" in
  ui)
    run_ui_tests
    ;;
  ui-coverage)
    run_ui_coverage
    ;;
  ui-watch)
    run_ui_watch
    ;;
  ui-component)
    run_ui_component "$2"
    ;;
  backend)
    run_backend_tests
    ;;
  all)
    run_all_tests
    ;;
  ci)
    run_ci_tests
    ;;
  help|--help|-h)
    usage
    ;;
  *)
    echo -e "${RED}Error: Invalid option${NC}"
    usage
    exit 1
    ;;
esac
