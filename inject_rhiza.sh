#!/bin/sh
# inject_rhiza.sh - Inject rhiza configuration templates into a repository
#
# This script automates the process of integrating rhiza templates into
# an existing Python project. It sets up the sync mechanism and performs
# an initial sync.
#
# Usage:
#   ./inject_rhiza.sh [OPTIONS] <target-directory>
#
# Options:
#   -h, --help           Show this help message
#   --branch BRANCH      Specify rhiza branch to use (default: main)
#
# Example:
#   # Inject rhiza into a project at /path/to/project
#   ./inject_rhiza.sh /path/to/project

set -e

BLUE="\033[36m"
RED="\033[31m"
GREEN="\033[32m"
YELLOW="\033[33m"
RESET="\033[0m"

RHIZA_REPO="jebel-quant/rhiza"
RHIZA_BRANCH="main"
TARGET_DIR=""

show_usage() {
  cat <<EOF
Usage: $0 [OPTIONS] <target-directory>

Inject rhiza configuration templates into an existing repository.

Arguments:
  target-directory     Path to the target repository

Options:
  -h, --help          Show this help message
  --branch BRANCH     Specify rhiza branch to use (default: main)

Example:
  # Inject rhiza into a project at /path/to/project
  $0 /path/to/project

  # Use a specific branch of rhiza
  $0 --branch develop /path/to/project

What this script does:
  1. Validates the target directory is a git repository
  2. Creates required directories (.github/workflows, .github/scripts)
  3. Creates a default template.yml configuration
  4. Performs sparse clone of files from rhiza (as listed in template.yml)
  5. Copies the fetched files to your repository

After running this script, you can:
  - Review changes with: git status
  - Customize .github/template.yml if needed
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

# Create required directories
printf "\n%b[INFO] Creating required directories...%b\n" "$BLUE" "$RESET"
mkdir -p "$TARGET_DIR/.github/workflows"
mkdir -p "$TARGET_DIR/.github/scripts"

# Create template.yml first so we know what to clone
TEMPLATE_FILE="$TARGET_DIR/.github/template.yml"
TEMPLATE_CREATED="true"

printf "%b[INFO] Creating default template.yml...%b\n" "$BLUE" "$RESET"

# Create a sensible default template.yml
cat > "$TEMPLATE_FILE" <<'EOF'
template-repository: "jebel-quant/rhiza"
template-branch: "main"
include: |
  .github
  .editorconfig
  .gitignore
  .pre-commit-config.yaml
  Makefile
  pytest.ini
EOF

printf "  %b[CREATE]%b .github/template.yml\n" "$GREEN" "$RESET"

# Perform sparse clone of files listed in template.yml
printf "\n%b[INFO] Fetching files from rhiza (sparse clone)...%b\n" "$BLUE" "$RESET"
RHIZA_URL="https://github.com/${RHIZA_REPO}.git"

# Initialize sparse checkout in temp directory
cd "$TEMP_DIR"
if ! git init >/dev/null 2>&1; then
  printf "%b[ERROR] Failed to initialize git repository%b\n" "$RED" "$RESET"
  exit 1
fi

# Configure sparse checkout
git config core.sparseCheckout true

# Specify which files to fetch (from the include section of template.yml)
cat > .git/info/sparse-checkout <<'SPARSE_EOF'
.github
.editorconfig
.gitignore
.pre-commit-config.yaml
Makefile
pytest.ini
SPARSE_EOF

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

# Copy files from temp directory to target
cd "$TARGET_DIR"
printf "%b[INFO] Copying files to target repository...%b\n" "$BLUE" "$RESET"

# Copy each file/directory from the sparse clone
for item in .github .editorconfig .gitignore .pre-commit-config.yaml Makefile pytest.ini; do
  if [ -e "$TEMP_DIR/$item" ]; then
    if [ -d "$TEMP_DIR/$item" ]; then
      # For directories, create destination and copy contents
      mkdir -p "$TARGET_DIR/$item"
      cp -R "$TEMP_DIR/$item"/. "$TARGET_DIR/$item"/
      printf "  %b[SYNC]%b %s (directory)\n" "$GREEN" "$RESET" "$item"
    else
      # For files, copy directly
      cp "$TEMP_DIR/$item" "$TARGET_DIR/$item"
      printf "  %b[SYNC]%b %s\n" "$GREEN" "$RESET" "$item"
    fi
  else
    printf "  %b[SKIP]%b %s (not found in rhiza)\n" "$YELLOW" "$RESET" "$item"
  fi
done

# Summary
printf "\n%b[SUCCESS] Rhiza injection complete!%b\n" "$GREEN" "$RESET"
printf "\nFiles synced from rhiza:\n"
printf "  ✓ .github/ (workflows and scripts)\n"
printf "  ✓ .editorconfig\n"
printf "  ✓ .gitignore\n"
printf "  ✓ .pre-commit-config.yaml\n"
printf "  ✓ Makefile\n"
printf "  ✓ pytest.ini\n"
printf "  ✓ .github/template.yml (created)\n"

# Next steps
printf "\n%b[NEXT STEPS]%b\n" "$BLUE" "$RESET"
printf "1. Review the changes:\n"
printf "   cd %s\n" "$TARGET_DIR"
printf "   git status\n"
printf "   git diff\n\n"

printf "2. Commit the changes:\n"
printf "   git add .\n"
printf "   git commit -m 'chore: integrate rhiza templates'\n\n"

printf "Next: (Optional) Set up automated sync workflow\n"
printf "      See: https://github.com/jebel-quant/rhiza#method-2-automated-sync-continuous-updates\n\n"

printf "%b[INFO] For more information, visit: https://github.com/jebel-quant/rhiza%b\n" "$BLUE" "$RESET"
