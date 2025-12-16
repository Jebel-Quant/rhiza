#!/bin/sh
# inject_rhiza.sh - Inject rhiza configuration templates into a repository
#
# This script automates the process of integrating rhiza templates into
# an existing Python project. It sets up the sync mechanism and optionally
# performs an initial sync.
#
# Usage:
#   ./inject_rhiza.sh [OPTIONS] <target-directory>
#
# Options:
#   -h, --help           Show this help message
#   --no-sync            Skip the initial sync after setup
#   --branch BRANCH      Specify rhiza branch to use (default: main)
#
# Example:
#   # Inject rhiza into a project at /path/to/project
#   ./inject_rhiza.sh /path/to/project
#
#   # Inject without running initial sync
#   ./inject_rhiza.sh --no-sync /path/to/project

set -e

BLUE="\033[36m"
RED="\033[31m"
GREEN="\033[32m"
YELLOW="\033[33m"
RESET="\033[0m"

RHIZA_REPO="jebel-quant/rhiza"
RHIZA_BRANCH="main"
DO_SYNC="true"
TARGET_DIR=""

show_usage() {
  cat <<EOF
Usage: $0 [OPTIONS] <target-directory>

Inject rhiza configuration templates into an existing repository.

Arguments:
  target-directory     Path to the target repository

Options:
  -h, --help          Show this help message
  --no-sync           Skip the initial sync after setup
  --branch BRANCH     Specify rhiza branch to use (default: main)

Example:
  # Inject rhiza into a project at /path/to/project
  $0 /path/to/project

  # Inject without running initial sync
  $0 --no-sync /path/to/project

  # Use a specific branch of rhiza
  $0 --branch develop /path/to/project

What this script does:
  1. Validates the target directory is a git repository
  2. Creates required directories (.github/workflows, .github/scripts)
  3. Copies sync.sh script from rhiza
  4. Creates a default template.yml configuration
  5. Optionally runs the initial sync

After running this script, you can:
  - Review changes with: git status
  - Customize .github/template.yml to select which files to sync
  - Run manual sync with: ./.github/scripts/sync.sh
  - Set up automated sync workflow (see rhiza documentation)
EOF
}

# Parse command line arguments
while [ $# -gt 0 ]; do
  case "$1" in
    -h|--help)
      show_usage
      exit 0
      ;;
    --no-sync)
      DO_SYNC="false"
      shift
      ;;
    --branch)
      if [ -z "$2" ]; then
        printf "%b[ERROR] --branch requires an argument%b\n" "$RED" "$RESET"
        exit 1
      fi
      RHIZA_BRANCH="$2"
      shift 2
      ;;
    -*)
      printf "%b[ERROR] Unknown option: %s%b\n" "$RED" "$1" "$RESET"
      show_usage
      exit 1
      ;;
    *)
      if [ -n "$TARGET_DIR" ]; then
        printf "%b[ERROR] Multiple target directories specified%b\n" "$RED" "$RESET"
        exit 1
      fi
      TARGET_DIR="$1"
      shift
      ;;
  esac
done

# Validate target directory is provided
if [ -z "$TARGET_DIR" ]; then
  printf "%b[ERROR] Target directory is required%b\n" "$RED" "$RESET"
  show_usage
  exit 1
fi

# Convert to absolute path
if [ ! -d "$TARGET_DIR" ]; then
  printf "%b[ERROR] Target directory does not exist: %s%b\n" "$RED" "$TARGET_DIR" "$RESET"
  exit 1
fi

# Make path absolute
TARGET_DIR=$(cd "$TARGET_DIR" && pwd)

printf "%b[INFO] Injecting rhiza into: %s%b\n" "$BLUE" "$TARGET_DIR" "$RESET"
printf "%b[INFO] Rhiza repository: %s%b\n" "$BLUE" "$RHIZA_REPO" "$RESET"
printf "%b[INFO] Rhiza branch: %s%b\n" "$BLUE" "$RHIZA_BRANCH" "$RESET"

# Check if target is a git repository
if [ ! -d "$TARGET_DIR/.git" ]; then
  printf "%b[ERROR] Target directory is not a git repository%b\n" "$RED" "$RESET"
  printf "Initialize a git repository first with: git init\n"
  exit 1
fi

# Check for uncommitted changes
cd "$TARGET_DIR"
# Check if there are any commits first (HEAD exists)
if git rev-parse HEAD >/dev/null 2>&1; then
  if ! git diff-index --quiet HEAD -- 2>/dev/null; then
    printf "%b[WARN] Target repository has uncommitted changes%b\n" "$YELLOW" "$RESET"
    printf "It's recommended to commit or stash changes before injection.\n"
    printf "Continue anyway? [y/N] "
    read -r answer
    case "$answer" in
      [Yy]*)
        printf "%b[INFO] Continuing with uncommitted changes...%b\n" "$YELLOW" "$RESET"
        ;;
      *)
        printf "%b[INFO] Aborting injection%b\n" "$BLUE" "$RESET"
        exit 0
        ;;
    esac
  fi
fi

# Create temporary directory for sparse clone
TEMP_DIR=$(mktemp -d)
trap 'rm -rf "$TEMP_DIR"' EXIT INT TERM

printf "\n%b[INFO] Fetching required files from rhiza (sparse clone)...%b\n" "$BLUE" "$RESET"
RHIZA_URL="https://github.com/${RHIZA_REPO}.git"

# Initialize sparse checkout
cd "$TEMP_DIR"
if ! git init >/dev/null 2>&1; then
  printf "%b[ERROR] Failed to initialize git repository%b\n" "$RED" "$RESET"
  exit 1
fi

# Configure sparse checkout
git config core.sparseCheckout true

# Specify which files to fetch
cat > .git/info/sparse-checkout <<EOF
.github/scripts/sync.sh
.github/template.yml
EOF

# Add remote and fetch only specified files
if ! git remote add origin "$RHIZA_URL" >/dev/null 2>&1; then
  printf "%b[ERROR] Failed to add remote%b\n" "$RED" "$RESET"
  exit 1
fi

if ! git fetch --depth 1 origin "$RHIZA_BRANCH" >/dev/null 2>&1; then
  printf "%b[ERROR] Failed to fetch from rhiza repository%b\n" "$RED" "$RESET"
  exit 1
fi

if ! git checkout "$RHIZA_BRANCH" >/dev/null 2>&1; then
  printf "%b[ERROR] Failed to checkout branch%b\n" "$RED" "$RESET"
  exit 1
fi

cd "$TARGET_DIR"

# Create required directories
printf "%b[INFO] Creating required directories...%b\n" "$BLUE" "$RESET"
mkdir -p "$TARGET_DIR/.github/workflows"
mkdir -p "$TARGET_DIR/.github/scripts"

# Copy sync.sh script
printf "%b[INFO] Copying sync.sh script...%b\n" "$BLUE" "$RESET"
if [ ! -f "$TEMP_DIR/.github/scripts/sync.sh" ]; then
  printf "%b[ERROR] sync.sh not found in rhiza repository%b\n" "$RED" "$RESET"
  exit 1
fi

cp "$TEMP_DIR/.github/scripts/sync.sh" "$TARGET_DIR/.github/scripts/sync.sh"
chmod +x "$TARGET_DIR/.github/scripts/sync.sh"
printf "  %b[COPY]%b .github/scripts/sync.sh\n" "$GREEN" "$RESET"

# Create or update template.yml
TEMPLATE_FILE="$TARGET_DIR/.github/template.yml"
TEMPLATE_CREATED="false"

if [ -f "$TEMPLATE_FILE" ]; then
  printf "%b[WARN] template.yml already exists, skipping creation%b\n" "$YELLOW" "$RESET"
  printf "  Existing file: %s\n" "$TEMPLATE_FILE"
else
  printf "%b[INFO] Creating default template.yml...%b\n" "$BLUE" "$RESET"
  
  # Check if rhiza has a template.yml to use as base
  if [ -f "$TEMP_DIR/.github/template.yml" ]; then
    cp "$TEMP_DIR/.github/template.yml" "$TEMPLATE_FILE"
    printf "  %b[COPY]%b .github/template.yml (from rhiza)\n" "$GREEN" "$RESET"
  else
    # Create a sensible default template.yml
    cat > "$TEMPLATE_FILE" <<'EOF'
template-repository: "jebel-quant/rhiza"
template-branch: "main"
include: |
  .github
  .devcontainer
  .editorconfig
  .gitignore
  .pre-commit-config.yaml
  CODE_OF_CONDUCT.md
  CONTRIBUTING.md
  Makefile
  docker
  pytest.ini
  ruff.toml
exclude: |
  .github/template.yml
EOF
    printf "  %b[CREATE]%b .github/template.yml (default)\n" "$GREEN" "$RESET"
  fi
  TEMPLATE_CREATED="true"
fi

# Summary
printf "\n%b[SUCCESS] Rhiza injection complete!%b\n" "$GREEN" "$RESET"
printf "\nFiles created/updated:\n"
printf "  ✓ .github/scripts/sync.sh\n"
if [ "$TEMPLATE_CREATED" = "true" ]; then
  printf "  ✓ .github/template.yml (created)\n"
else
  printf "  - .github/template.yml (already exists)\n"
fi

# Run initial sync if requested
if [ "$DO_SYNC" = "true" ]; then
  printf "\n%b[INFO] Running initial sync...%b\n" "$BLUE" "$RESET"
  printf "This will download and apply templates from rhiza.\n"
  
  if ! "$TARGET_DIR/.github/scripts/sync.sh"; then
    printf "%b[ERROR] Initial sync failed%b\n" "$RED" "$RESET"
    exit 1
  fi
  
  printf "\n%b[INFO] Initial sync complete!%b\n" "$GREEN" "$RESET"
else
  printf "\n%b[INFO] Skipping initial sync (--no-sync flag used)%b\n" "$YELLOW" "$RESET"
fi

# Next steps
printf "\n%b[NEXT STEPS]%b\n" "$BLUE" "$RESET"
printf "1. Review the changes:\n"
printf "   cd %s\n" "$TARGET_DIR"
printf "   git status\n"
printf "   git diff\n\n"

if [ "$DO_SYNC" = "false" ]; then
  printf "2. Customize .github/template.yml to select which files to sync\n\n"
  printf "3. Run the initial sync:\n"
  printf "   ./.github/scripts/sync.sh\n\n"
  printf "4. Review and commit the changes:\n"
  printf "   git add .\n"
  printf "   git commit -m 'chore: integrate rhiza templates'\n\n"
else
  printf "2. Commit the changes:\n"
  printf "   git add .\n"
  printf "   git commit -m 'chore: integrate rhiza templates'\n\n"
fi

printf "Next: (Optional) Set up automated sync workflow\n"
printf "      See: https://github.com/jebel-quant/rhiza#method-2-automated-sync-continuous-updates\n\n"

printf "%b[INFO] For more information, visit: https://github.com/jebel-quant/rhiza%b\n" "$BLUE" "$RESET"
