#!/usr/bin/env bash
# GitLab CI Workflow Validation Script
#
# This script validates the GitLab CI/CD workflow configuration files.
# It checks YAML syntax, file structure, and provides a summary report.
#
# Usage: bash .gitlab/validate.sh

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Counters
TOTAL_FILES=0
VALID_FILES=0
INVALID_FILES=0

echo -e "${BLUE}=== GitLab CI/CD Workflow Validation ===${NC}\n"

# Function to validate YAML syntax
validate_yaml() {
    local file="$1"
    TOTAL_FILES=$((TOTAL_FILES + 1))
    
    if python3 -c "import yaml; yaml.safe_load(open('$file'))" 2>/dev/null; then
        echo -e "${GREEN}✅ $file${NC}"
        VALID_FILES=$((VALID_FILES + 1))
        return 0
    else
        echo -e "${RED}❌ $file - YAML syntax error${NC}"
        INVALID_FILES=$((INVALID_FILES + 1))
        return 1
    fi
}

# Check if required tools are available
echo -e "${BLUE}Checking required tools...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ python3 is not installed${NC}"
    exit 1
fi

if ! python3 -c "import yaml" &> /dev/null; then
    echo -e "${YELLOW}⚠️  PyYAML not installed, installing...${NC}"
    python3 -m pip install --quiet pyyaml
fi

echo -e "${GREEN}✅ All required tools are available${NC}\n"

# Validate main configuration
echo -e "${BLUE}Validating main configuration...${NC}"
if [ -f ".gitlab-ci.yml" ]; then
    validate_yaml ".gitlab-ci.yml"
else
    echo -e "${RED}❌ .gitlab-ci.yml not found${NC}"
    exit 1
fi
echo ""

# Validate workflow files
echo -e "${BLUE}Validating workflow files...${NC}"
if [ -d ".gitlab/workflows" ]; then
    for file in .gitlab/workflows/*.yml; do
        if [ -f "$file" ]; then
            validate_yaml "$file"
        fi
    done
else
    echo -e "${RED}❌ .gitlab/workflows directory not found${NC}"
    exit 1
fi
echo ""

# Check documentation
echo -e "${BLUE}Checking documentation...${NC}"
DOCS=(
    ".gitlab/README.md"
    ".gitlab/TESTING.md"
    ".gitlab/COMPARISON.md"
    "GITLAB_CI.md"
)

for doc in "${DOCS[@]}"; do
    if [ -f "$doc" ]; then
        echo -e "${GREEN}✅ $doc${NC}"
    else
        echo -e "${YELLOW}⚠️  $doc not found${NC}"
    fi
done
echo ""

# Check workflow file count
echo -e "${BLUE}Workflow summary...${NC}"
WORKFLOW_COUNT=$(find .gitlab/workflows -name "*.yml" -type f | wc -l)
echo -e "Total workflow files: ${GREEN}$WORKFLOW_COUNT${NC}"

# Expected workflows
EXPECTED_WORKFLOWS=(
    "rhiza_ci.yml"
    "rhiza_devcontainer.yml"
    "rhiza_marimo.yml"
    "rhiza_validate.yml"
    "rhiza_deptry.yml"
    "rhiza_docker.yml"
    "rhiza_pre-commit.yml"
    "rhiza_book.yml"
    "rhiza_sync.yml"
    "rhiza_release.yml"
)

echo -e "\n${BLUE}Checking for expected workflows...${NC}"
for workflow in "${EXPECTED_WORKFLOWS[@]}"; do
    if [ -f ".gitlab/workflows/$workflow" ]; then
        echo -e "${GREEN}✅ $workflow${NC}"
    else
        echo -e "${RED}❌ $workflow not found${NC}"
    fi
done
echo ""

# Check for GitHub Actions equivalents
echo -e "${BLUE}Checking GitHub Actions equivalents...${NC}"
if [ -d ".github/workflows" ]; then
    GITHUB_COUNT=$(find .github/workflows -name "rhiza_*.yml" -type f | wc -l)
    echo -e "GitHub Actions workflows: ${GREEN}$GITHUB_COUNT${NC}"
    echo -e "GitLab CI workflows: ${GREEN}$WORKFLOW_COUNT${NC}"
    
    if [ "$GITHUB_COUNT" -eq "$WORKFLOW_COUNT" ]; then
        echo -e "${GREEN}✅ Workflow count matches${NC}"
    else
        echo -e "${YELLOW}⚠️  Workflow count mismatch${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  .github/workflows directory not found${NC}"
fi
echo ""

# Final summary
echo -e "${BLUE}=== Validation Summary ===${NC}"
echo -e "Total files validated: $TOTAL_FILES"
echo -e "${GREEN}Valid files: $VALID_FILES${NC}"

if [ "$INVALID_FILES" -gt 0 ]; then
    echo -e "${RED}Invalid files: $INVALID_FILES${NC}"
    echo -e "\n${RED}❌ Validation failed${NC}"
    exit 1
else
    echo -e "${GREEN}Invalid files: 0${NC}"
    echo -e "\n${GREEN}✅ All validations passed!${NC}"
    echo -e "${BLUE}Next steps:${NC}"
    echo -e "  1. Set up a GitLab repository (mirror or fork)"
    echo -e "  2. Configure CI/CD variables (see .gitlab/README.md)"
    echo -e "  3. Push code to trigger pipelines"
    echo -e "  4. Follow testing guide (.gitlab/TESTING.md)"
    exit 0
fi
