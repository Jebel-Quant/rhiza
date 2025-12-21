#!/bin/sh
# Changelog generation script
# - Generates/updates CHANGELOG.md using git-cliff
# - Can generate for unreleased changes, specific tag, or full history
#
# This script is POSIX-sh compatible and follows the style of other scripts
# in this repository. It uses uvx to run git-cliff.

set -e

UVX_BIN=${UVX_BIN:-./bin/uvx}

BLUE="\033[36m"
RED="\033[31m"
GREEN="\033[32m"
YELLOW="\033[33m"
RESET="\033[0m"

# Default options
MODE="unreleased"
TAG=""
OUTPUT="CHANGELOG.md"

# Parse command-line arguments
show_usage() {
  printf "Usage: %s [OPTIONS]\n\n" "$0"
  printf "Description:\n"
  printf "  Generate or update CHANGELOG.md using git-cliff\n\n"
  printf "Options:\n"
  printf "  -m, --mode MODE       Generation mode: unreleased|tag|full (default: unreleased)\n"
  printf "  -t, --tag TAG         Generate changelog for specific tag (requires --mode tag)\n"
  printf "  -o, --output FILE     Output file (default: CHANGELOG.md)\n"
  printf "  -h, --help            Show this help message\n\n"
  printf "Modes:\n"
  printf "  unreleased            Generate changelog for unreleased changes only\n"
  printf "  tag                   Generate changelog up to a specific tag\n"
  printf "  full                  Generate full changelog from all history\n\n"
  printf "Examples:\n"
  printf "  %s                                      (generate unreleased changes)\n" "$0"
  printf "  %s --mode full                          (regenerate full changelog)\n" "$0"
  printf "  %s --mode tag --tag v0.3.0              (generate up to v0.3.0)\n" "$0"
}

while [ $# -gt 0 ]; do
  case "$1" in
    -m|--mode)
      if [ -z "$2" ] || [ "${2#-}" != "$2" ]; then
        printf "%b[ERROR] --mode requires a value%b\n" "$RED" "$RESET"
        show_usage
        exit 1
      fi
      MODE="$2"
      shift 2
      ;;
    -t|--tag)
      if [ -z "$2" ] || [ "${2#-}" != "$2" ]; then
        printf "%b[ERROR] --tag requires a value%b\n" "$RED" "$RESET"
        show_usage
        exit 1
      fi
      TAG="$2"
      shift 2
      ;;
    -o|--output)
      if [ -z "$2" ] || [ "${2#-}" != "$2" ]; then
        printf "%b[ERROR] --output requires a value%b\n" "$RED" "$RESET"
        show_usage
        exit 1
      fi
      OUTPUT="$2"
      shift 2
      ;;
    -h|--help)
      show_usage
      exit 0
      ;;
    -*)
      printf "%b[ERROR] Unknown option: %s%b\n" "$RED" "$1" "$RESET"
      show_usage
      exit 1
      ;;
    *)
      printf "%b[ERROR] Unknown argument: %s%b\n" "$RED" "$1" "$RESET"
      show_usage
      exit 1
      ;;
  esac
done

# Check if uvx is available
if [ ! -x "$UVX_BIN" ]; then
  printf "%b[ERROR] uvx not found at %s. Run 'make install-uv' first.%b\n" "$RED" "$UVX_BIN" "$RESET"
  exit 1
fi

# Check if cliff.toml exists
if [ ! -f "cliff.toml" ]; then
  printf "%b[ERROR] cliff.toml not found in current directory%b\n" "$RED" "$RESET"
  exit 1
fi

# Generate changelog based on mode
case "$MODE" in
  unreleased)
    printf "%b[INFO] Generating changelog for unreleased changes...%b\n" "$BLUE" "$RESET"
    "$UVX_BIN" git-cliff --unreleased --prepend "$OUTPUT"
    ;;
  tag)
    if [ -z "$TAG" ]; then
      printf "%b[ERROR] --tag is required when using --mode tag%b\n" "$RED" "$RESET"
      exit 1
    fi
    printf "%b[INFO] Generating changelog up to tag %s...%b\n" "$BLUE" "$TAG" "$RESET"
    "$UVX_BIN" git-cliff --tag "$TAG" --output "$OUTPUT"
    ;;
  full)
    printf "%b[INFO] Generating full changelog from all history...%b\n" "$BLUE" "$RESET"
    "$UVX_BIN" git-cliff --output "$OUTPUT"
    ;;
  *)
    printf "%b[ERROR] Invalid mode: %s%b\n" "$RED" "$MODE" "$RESET"
    printf "Valid modes: unreleased, tag, full\n"
    exit 1
    ;;
esac

printf "%b[SUCCESS] Changelog generated: %s%b\n" "$GREEN" "$OUTPUT" "$RESET"
