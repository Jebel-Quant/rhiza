#!/usr/bin/env bash
# inject_rhiza.sh — Materialize rhiza configuration templates via sparse checkout
#
# This script performs a one-shot import of selected files from the rhiza
# template repository into an existing git repository.
#
# No sync engine. No background coupling. Git-native snapshot semantics.
#
# Usage:
#   ./inject_rhiza.sh [OPTIONS] <target-directory>
#
# Options:
#   --branch BRANCH     Rhiza branch to use (default: main)
#   --force, -y         Overwrite existing files without prompting
#   -h, --help          Show help

set -euo pipefail

# ------------------------------------------------------------------------------
# Configuration
# ------------------------------------------------------------------------------

RHIZA_REPO="jebel-quant/rhiza"
RHIZA_BRANCH="main"
FORCE="false"
TARGET_DIR=""

BLUE="\033[36m"
RED="\033[31m"
GREEN="\033[32m"
YELLOW="\033[33m"
RESET="\033[0m"

# ------------------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------------------

die() {
  printf "%b[ERROR]%b %s\n" "$RED" "$RESET" "$1" >&2
  exit 1
}

info() {
  printf "%b[INFO]%b %s\n" "$BLUE" "$RESET" "$1"
}

warn() {
  printf "%b[WARN]%b %s\n" "$YELLOW" "$RESET" "$1"
}

success() {
  printf "%b[SUCCESS]%b %s\n" "$GREEN" "$RESET" "$1"
}

show_usage() {
  cat <<EOF
Usage: $0 [OPTIONS] <target-directory>

Materialize rhiza configuration templates into an existing git repository
using git sparse checkout (one-shot import).

Options:
  --branch BRANCH     Rhiza branch to use (default: main)
  --force, -y         Overwrite existing files without prompting
  -h, --help          Show this help message

Example:
  $0 /path/to/project
  $0 --branch develop --force /path/to/project

What this script does:
  1. Validates the target is a git repository
  2. Writes .github/template.yml (if missing)
  3. Performs a sparse checkout of rhiza
  4. Copies selected files into the target repo
  5. Leaves no external git state behind

No sync engine. No automation. Explicit snapshot semantics.
EOF
}

# ------------------------------------------------------------------------------
# Parse arguments
# ------------------------------------------------------------------------------

while [ $# -gt 0 ]; do
  case "$1" in
    --branch)
      [ $# -ge 2 ] || die "--branch requires an argument"
      RHIZA_BRANCH="$2"
      shift 2
      ;;
    --force|-y)
      FORCE="true"
      shift
      ;;
    -h|--help)
      show_usage
      exit 0
      ;;
    -*)
      die "Unknown option: $1"
      ;;
    *)
      [ -z "$TARGET_DIR" ] || die "Multiple target directories specified"
      TARGET_DIR="$1"
      shift
      ;;
  esac
done

[ -n "$TARGET_DIR" ] || die "Target directory is required"

# ------------------------------------------------------------------------------
# Validate target repository
# ------------------------------------------------------------------------------

[ -d "$TARGET_DIR" ] || die "Target directory does not exist: $TARGET_DIR"
TARGET_DIR="$(cd "$TARGET_DIR" && pwd)"

[ -d "$TARGET_DIR/.git" ] || die "Target directory is not a git repository"

info "Target repository: $TARGET_DIR"
info "Rhiza repository: $RHIZA_REPO"
info "Rhiza branch:     $RHIZA_BRANCH"

# ------------------------------------------------------------------------------
# Ensure template.yml exists
# ------------------------------------------------------------------------------

TEMPLATE_FILE="$TARGET_DIR/.github/template.yml"

if [ ! -f "$TEMPLATE_FILE" ]; then
  info "Creating default .github/template.yml"
  mkdir -p "$TARGET_DIR/.github"

  cat > "$TEMPLATE_FILE" <<EOF
template-repository: "$RHIZA_REPO"
template-branch: "$RHIZA_BRANCH"
include: |
  .github
  .editorconfig
  .gitignore
  .pre-commit-config.yaml
  Makefile
  pytest.ini
EOF

  printf "  %b[CREATE]%b .github/template.yml\n" "$GREEN" "$RESET"
else
  info "Using existing .github/template.yml"
fi

# ------------------------------------------------------------------------------
# Extract values from template.yml
# ------------------------------------------------------------------------------

extract_value() {
  awk -F': ' "/^$1:/ {print \$2}" "$TEMPLATE_FILE" | tr -d '"'
}

extract_include() {
  awk '
    /^include:/ {flag=1; next}
    flag && /^[^ ]/ {exit}
    flag {sub(/^  /,""); print}
  ' "$TEMPLATE_FILE"
}

RHIZA_REPO="$(extract_value template-repository)"
RHIZA_BRANCH="$(extract_value template-branch)"

INCLUDE_PATHS="$(extract_include)"

[ -n "$INCLUDE_PATHS" ] || die "No include paths found in template.yml"

info "Include paths:"
printf "%s\n" "$INCLUDE_PATHS" | sed 's/^/  - /'

# ------------------------------------------------------------------------------
# Sparse clone rhiza
# ------------------------------------------------------------------------------

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

info "Performing sparse clone of rhiza"

git clone \
  --depth 1 \
  --filter=blob:none \
  --sparse \
  --branch "$RHIZA_BRANCH" \
  "https://github.com/${RHIZA_REPO}.git" \
  "$TMP_DIR" \
  >/dev/null

cd "$TMP_DIR"
git sparse-checkout init --cone
git sparse-checkout set $INCLUDE_PATHS

# ------------------------------------------------------------------------------
# Copy files into target repo
# ------------------------------------------------------------------------------

cd "$TARGET_DIR"

for path in $INCLUDE_PATHS; do
  src="$TMP_DIR/$path"
  dst="$TARGET_DIR/$path"

  if [ ! -e "$src" ]; then
    warn "$path not found in rhiza — skipping"
    continue
  fi

  if [ -e "$dst" ] && [ "$FORCE" != "true" ]; then
    warn "$path already exists — use --force to overwrite"
    continue
  fi

  mkdir -p "$(dirname "$dst")"
  rm -rf "$dst"
  cp -R "$src" "$dst"

  printf "  %b[ADD]%b %s\n" "$GREEN" "$RESET" "$path"
done

# ------------------------------------------------------------------------------
# Done
# ------------------------------------------------------------------------------

success "Rhiza templates materialized successfully"

cat <<EOF

Next steps:
  1. Review changes:
       git status
       git diff

  2. Commit:
       git add .
       git commit -m "chore: import rhiza templates"

This is a one-shot snapshot.
Re-run this script to update templates explicitly.
EOF
