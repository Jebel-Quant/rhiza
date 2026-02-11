#!/bin/sh
# ============================================================================
# RELEASE SCRIPT
# ============================================================================
# 
# This script automates the process of creating and publishing a release:
#   1. Reads version from pyproject.toml using uv
#   2. Creates a git tag (v{version}) with optional GPG signing
#   3. Pushes the tag to remote to trigger GitHub Actions release workflow
#
# SAFETY CHECKS:
#   - Verifies clean working directory (no uncommitted changes)
#   - Ensures branch is in sync with remote (not behind/diverged)
#   - Validates tag doesn't already exist locally or remotely
#   - Warns if releasing from non-default branch
#
# USAGE:
#   ./release.sh           # Interactive mode with prompts
#   ./release.sh --dry-run # Simulate without making changes
#   ./release.sh --help    # Show usage information
#
# REQUIREMENTS:
#   - uv must be installed (via make install-uv)
#   - pyproject.toml must exist with valid version
#   - Git repository with configured remote
#
# NOTE: This script is POSIX-sh compatible for maximum portability
#
# ============================================================================

# Exit on error and undefined variables
set -eu

# ============================================================================
# CONFIGURATION
# ============================================================================

# Path to uv binary (can be overridden via UV_BIN environment variable)
UV_BIN=${UV_BIN:-./bin/uv}

# Dry-run mode flag (set by --dry-run flag)
DRY_RUN=""

# ANSI color codes for terminal output
BLUE="\033[36m"
RED="\033[31m"
GREEN="\033[32m"
YELLOW="\033[33m"
RESET="\033[0m"

# ============================================================================
# COMMAND-LINE ARGUMENT PARSING
# ============================================================================

# Display usage information
show_usage() {
  printf "Usage: %s [OPTIONS]\n\n" "$0"
  printf "Description:\n"
  printf "  Create tag and push to remote (with prompts)\n\n"
  printf "Options:\n"
  printf "  -n, --dry-run  Show what would be done without making changes\n"
  printf "  -h, --help     Show this help message\n\n"
  printf "Examples:\n"
  printf "  %s                                      (create tag and push with prompts)\n" "$0"
  printf "  %s --dry-run                            (simulate release without changes)\n" "$0"
}

# Parse command-line arguments
while [ $# -gt 0 ]; do
  case "$1" in
    -n|--dry-run)
      DRY_RUN="true"
      shift
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

# ============================================================================
# PREREQUISITE CHECKS
# ============================================================================

# Verify pyproject.toml exists (required for version extraction)
if [ ! -f "pyproject.toml" ]; then
  printf "%b[ERROR] pyproject.toml not found in current directory%b\n" "$RED" "$RESET"
  exit 1
fi

# Verify uv is installed and executable
if [ ! -x "$UV_BIN" ]; then
  printf "%b[ERROR] uv not found at %s. Run 'make install-uv' first.%b\n" "$RED" "$UV_BIN" "$RESET"
  exit 1
fi

# ============================================================================
# HELPER FUNCTIONS - USER PROMPTS
# ============================================================================

# Prompt user to continue or abort
# In dry-run mode, automatically continues without prompting
# Args:
#   $1 - Message to display to user
# Returns:
#   0 if user confirms (y/Y) or in dry-run mode
#   Exits script if user declines
prompt_continue() {
  _pc_message="$1"
  if [ -n "$DRY_RUN" ]; then
    printf "\n%b[DRY-RUN] %s Would prompt to continue%b\n" "$YELLOW" "$_pc_message" "$RESET"
    return 0
  fi
  printf "\n%b[PROMPT] %s Continue? [y/N] %b" "$YELLOW" "$_pc_message" "$RESET"
  read -r _pc_answer
  case "$_pc_answer" in
    [Yy]*)
      return 0
      ;;
    *)
      printf "%b[INFO] Aborted by user%b\n" "$YELLOW" "$RESET"
      exit 0
      ;;
  esac
}

# Prompt user for yes/no confirmation
# In dry-run mode, automatically returns yes
# Args:
#   $1 - Message to display to user
# Returns:
#   0 if user confirms (y/Y) or in dry-run mode
#   1 if user declines
prompt_yes_no() {
  _pyn_message="$1"
  if [ -n "$DRY_RUN" ]; then
    printf "\n%b[DRY-RUN] %s Would prompt yes/no%b\n" "$YELLOW" "$_pyn_message" "$RESET"
    return 0
  fi
  printf "\n%b[PROMPT] %s [y/N] %b" "$YELLOW" "$_pyn_message" "$RESET"
  read -r _pyn_answer
  case "$_pyn_answer" in
    [Yy]*)
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

# ============================================================================
# VERSION AND TAG RETRIEVAL
# ============================================================================

# Get the current version from pyproject.toml and format as a git tag
# Side effects: Sets CURRENT_VERSION and TAG global variables
get_version_and_tag() {
  # Use uv to extract version from pyproject.toml
  CURRENT_VERSION=$("$UV_BIN" version --short 2>/dev/null)
  if [ -z "$CURRENT_VERSION" ]; then
    printf "%b[ERROR] Could not determine version from pyproject.toml%b\n" "$RED" "$RESET"
    exit 1
  fi
  
  # Format tag with 'v' prefix (e.g., v1.2.3)
  TAG="v$CURRENT_VERSION"
  
  printf "%b[INFO] Current version: %s%b\n" "$BLUE" "$CURRENT_VERSION" "$RESET"
  printf "%b[INFO] Tag to create: %s%b\n" "$BLUE" "$TAG" "$RESET"
}

# ============================================================================
# BRANCH VALIDATION
# ============================================================================

# Validate that the current branch is appropriate for creating a release
# Warns if not on the default branch but allows user to proceed
# Side effects: Sets CURRENT_BRANCH and DEFAULT_BRANCH global variables
validate_branch() {
  # Get the name of the current branch
  CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
  if [ -z "$CURRENT_BRANCH" ]; then
    printf "%b[ERROR] Could not determine current branch%b\n" "$RED" "$RESET"
    exit 1
  fi

  # Query remote to determine the default branch (main, master, etc.)
  DEFAULT_BRANCH=$(git remote show origin | grep 'HEAD branch' | cut -d' ' -f5)
  if [ -z "$DEFAULT_BRANCH" ]; then
    printf "%b[ERROR] Could not determine default branch from remote%b\n" "$RED" "$RESET"
    exit 1
  fi

  # Warn if attempting to release from a non-default branch
  # This is usually not recommended but may be necessary in some workflows
  if [ "$CURRENT_BRANCH" != "$DEFAULT_BRANCH" ]; then
    printf "%b[WARN] You are on branch '%s' but the default branch is '%s'%b\n" "$YELLOW" "$CURRENT_BRANCH" "$DEFAULT_BRANCH" "$RESET"
    printf "%b[WARN] Releases are typically created from the default branch.%b\n" "$YELLOW" "$RESET"
    prompt_continue "Proceed with release from '$CURRENT_BRANCH'?"
  fi
}

# ============================================================================
# GIT STATUS CHECKS
# ============================================================================

# Check for uncommitted changes in the working directory
# Releases must be created from a clean working tree
check_uncommitted_changes() {
  if [ -n "$(git status --porcelain)" ]; then
    printf "%b[ERROR] You have uncommitted changes:%b\n" "$RED" "$RESET"
    git status --short
    printf "\n%b[ERROR] Please commit or stash your changes before releasing.%b\n" "$RED" "$RESET"
    exit 1
  fi
}

# ============================================================================
# UPSTREAM SYNCHRONIZATION CHECK
# ============================================================================

# Verify that the local branch is in sync with its remote tracking branch
# This prevents releases from out-of-date or diverged branches
# Handles three scenarios:
#   1. Local is behind remote → Error (must pull first)
#   2. Local is ahead of remote → Prompt to push changes
#   3. Branches have diverged → Error (must reconcile)
check_upstream_sync() {
  printf "%b[INFO] Checking remote status...%b\n" "$BLUE" "$RESET"
  
  # Fetch latest changes from remote without merging
  git fetch origin >/dev/null 2>&1
  
  # Get the upstream tracking branch (e.g., origin/main)
  UPSTREAM=$(git rev-parse --abbrev-ref --symbolic-full-name '@{u}' 2>/dev/null)
  if [ -z "$UPSTREAM" ]; then
    printf "%b[ERROR] No upstream branch configured for %s%b\n" "$RED" "$CURRENT_BRANCH" "$RESET"
    exit 1
  fi
  
  # Get commit SHAs for comparison
  # LOCAL: current commit on local branch
  # REMOTE: current commit on remote tracking branch
  # BASE: most recent common ancestor between local and remote
  LOCAL=$(git rev-parse @)
  REMOTE=$(git rev-parse "$UPSTREAM")
  BASE=$(git merge-base @ "$UPSTREAM")
  
  # Compare commits to determine sync status
  if [ "$LOCAL" = "$REMOTE" ]; then
    # Branches are in sync - no action needed
    return 0
  fi
  
  # Branches are not in sync - determine the type of divergence
  if [ "$LOCAL" = "$BASE" ]; then
    # Local is behind remote (need to pull)
    printf "%b[ERROR] Your branch is behind '%s'. Please pull changes.%b\n" "$RED" "$UPSTREAM" "$RESET"
    exit 1
  elif [ "$REMOTE" = "$BASE" ]; then
    # Local is ahead of remote (need to push)
    printf "%b[WARN] Your branch is ahead of '%s'.%b\n" "$YELLOW" "$UPSTREAM" "$RESET"
    printf "Unpushed commits:\n"
    git log --oneline --graph --decorate "$UPSTREAM..HEAD"
    prompt_continue "Push changes to remote before releasing?"
    
    if [ -n "$DRY_RUN" ]; then
      printf "%b[DRY-RUN] Would run: git push origin %s%b\n" "$YELLOW" "$CURRENT_BRANCH" "$RESET"
    else
      git push origin "$CURRENT_BRANCH"
    fi
  else
    # Branches have diverged (need to merge or rebase)
    printf "%b[ERROR] Your branch has diverged from '%s'. Please reconcile.%b\n" "$RED" "$UPSTREAM" "$RESET"
    exit 1
  fi
}

# ============================================================================
# TAG VALIDATION
# ============================================================================

# Check if the release tag already exists locally or remotely
# Side effects: Sets SKIP_TAG_CREATE variable if tag exists locally
check_tag_exists() {
  SKIP_TAG_CREATE=""
  
  # Check if tag already exists locally
  if git rev-parse "$TAG" >/dev/null 2>&1; then
    printf "%b[WARN] Tag '%s' already exists locally%b\n" "$YELLOW" "$TAG" "$RESET"
    prompt_continue "Tag exists. Skip tag creation and proceed to push?"
    SKIP_TAG_CREATE="true"
  fi

  # Check if tag already exists on remote
  # If it does, the release has already been published
  if git ls-remote --exit-code --tags origin "refs/tags/$TAG" >/dev/null 2>&1; then
    printf "%b[ERROR] Tag '%s' already exists on remote%b\n" "$RED" "$TAG" "$RESET"
    printf "The release for version %s has already been published.\n" "$CURRENT_VERSION"
    exit 1
  fi
}

# ============================================================================
# TAG CREATION
# ============================================================================

# Create a git tag for the release
# Automatically uses GPG signing if configured
create_release_tag() {
  # Skip tag creation if it already exists locally
  if [ -n "$SKIP_TAG_CREATE" ]; then
    return 0
  fi
  
  printf "\n%b=== Step 1: Create Tag ===%b\n" "$BLUE" "$RESET"
  printf "Creating tag '%s' for version %s\n" "$TAG" "$CURRENT_VERSION"
  prompt_continue ""
  
  # Determine if GPG signing is configured
  # Signed tags provide cryptographic verification of release authenticity
  if git config --get user.signingkey >/dev/null 2>&1 || [ "$(git config --get commit.gpgsign)" = "true" ]; then
    # Create signed tag with -s flag
    printf "%b[INFO] GPG signing is enabled. Creating signed tag.%b\n" "$BLUE" "$RESET"
    if [ -n "$DRY_RUN" ]; then
      printf "%b[DRY-RUN] Would run: git tag -s %s -m \"Release %s\"%b\n" "$YELLOW" "$TAG" "$TAG" "$RESET"
    else
      git tag -s "$TAG" -m "Release $TAG"
    fi
  else
    # Create annotated tag with -a flag (no signature)
    printf "%b[INFO] GPG signing is not enabled. Creating unsigned tag.%b\n" "$BLUE" "$RESET"
    if [ -n "$DRY_RUN" ]; then
      printf "%b[DRY-RUN] Would run: git tag -a %s -m \"Release %s\"%b\n" "$YELLOW" "$TAG" "$TAG" "$RESET"
    else
      git tag -a "$TAG" -m "Release $TAG"
    fi
  fi
  
  # Report success
  if [ -n "$DRY_RUN" ]; then
    printf "%b[DRY-RUN] Tag '%s' would be created locally%b\n" "$YELLOW" "$TAG" "$RESET"
  else
    printf "%b[SUCCESS] Tag '%s' created locally%b\n" "$GREEN" "$TAG" "$RESET"
  fi
}

# ============================================================================
# TAG PUSH
# ============================================================================

# Push the release tag to the remote repository
# This triggers the GitHub Actions release workflow
push_release_tag() {
  printf "\n%b=== Step 2: Push Tag to Remote ===%b\n" "$BLUE" "$RESET"
  printf "Pushing tag '%s' to origin will trigger the release workflow.\n" "$TAG"
  
  # Show what commits are in this tag compared to the last tag
  # This helps users understand what changes are included in the release
  LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
  if [ -n "$LAST_TAG" ] && [ "$LAST_TAG" != "$TAG" ]; then
    COMMIT_COUNT=$(git rev-list "$LAST_TAG..$TAG" --count 2>/dev/null || echo "0")
    printf "Commits since %s: %s\n" "$LAST_TAG" "$COMMIT_COUNT"
  fi
  
  prompt_continue ""

  # Extract repository name from remote URL for constructing GitHub Actions link
  # Converts git@github.com:user/repo.git or https://github.com/user/repo.git to user/repo
  REPO_URL=$(git remote get-url origin | sed 's/.*github.com[:/]\(.*\)\.git/\1/')

  # Push only the specific tag (not all tags) to trigger the release workflow
  if [ -n "$DRY_RUN" ]; then
    printf "%b[DRY-RUN] Would run: git push origin refs/tags/%s%b\n" "$YELLOW" "$TAG" "$RESET"
    printf "\n%b[DRY-RUN] Release tag %s would be pushed to remote%b\n" "$YELLOW" "$TAG" "$RESET"
    printf "%b[DRY-RUN] This would trigger the release workflow%b\n" "$YELLOW" "$RESET"
    printf "%b[INFO] Monitor progress at: https://github.com/%s/actions%b\n" "$BLUE" "$REPO_URL" "$RESET"
  else
    git push origin "refs/tags/$TAG"
    printf "\n%b[SUCCESS] Release tag %s pushed to remote!%b\n" "$GREEN" "$TAG" "$RESET"
    printf "%b[INFO] The release workflow will now be triggered automatically.%b\n" "$BLUE" "$RESET"
    printf "%b[INFO] Monitor progress at: https://github.com/%s/actions%b\n" "$BLUE" "$REPO_URL" "$RESET"
  fi
}

# ============================================================================
# MAIN RELEASE ORCHESTRATION
# ============================================================================

# Orchestrate the release process by calling helper functions in sequence
# This function coordinates all the steps required to create and push a release tag
do_release() {
  # Step 1: Get version information and format tag
  get_version_and_tag
  
  # Step 2: Validate that we're on an appropriate branch
  validate_branch
  
  # Step 3: Ensure working directory is clean
  check_uncommitted_changes
  
  # Step 4: Verify local branch is in sync with remote
  check_upstream_sync
  
  # Step 5: Check if tag already exists
  check_tag_exists
  
  # Step 6: Create the git tag
  create_release_tag
  
  # Step 7: Push tag to remote (triggers release workflow)
  push_release_tag
}

# Main execution logic
do_release
