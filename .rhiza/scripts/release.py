#!/usr/bin/env python3
"""Release script for creating and pushing git tags.

This script:
- Creates a git tag based on the current version in pyproject.toml
- Pushes the tag to remote to trigger the release workflow
- Performs checks (branch, upstream status, clean working tree)
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path


class Colors:
    """ANSI color codes for terminal output."""

    BLUE = "\033[36m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    RESET = "\033[0m"


def print_colored(color: str, message: str) -> None:
    """Print a colored message to stdout."""
    print(f"{color}{message}{Colors.RESET}")


def run_command(
    cmd: list[str], cwd: Path | None = None, check: bool = True, capture_output: bool = True
) -> subprocess.CompletedProcess:
    """Run a command and return the result.

    Args:
        cmd: Command and arguments to run
        cwd: Working directory for the command
        check: Raise exception on non-zero exit code
        capture_output: Capture stdout and stderr

    Returns:
        CompletedProcess instance with result
    """
    return subprocess.run(
        cmd,
        cwd=cwd,
        check=check,
        capture_output=capture_output,
        text=True,
    )


def prompt_continue(message: str) -> bool:
    """Prompt user to continue with an operation.

    Args:
        message: Message to display to user (optional)

    Returns:
        True if user wants to continue, False otherwise
    """
    if message:
        prompt_text = f"[PROMPT] {message} Continue? [y/N] "
    else:
        prompt_text = "[PROMPT] Continue? [y/N] "
    print()  # Print newline before prompt
    print_colored(Colors.YELLOW, prompt_text)
    answer = input().strip().lower()
    if answer in ("y", "yes"):
        return True
    print_colored(Colors.YELLOW, "[INFO] Aborted by user")
    return False


def get_version(uv_bin: str) -> str:
    """Get the current version from pyproject.toml using uv.

    Args:
        uv_bin: Path to uv binary

    Returns:
        Version string

    Raises:
        SystemExit: If version cannot be determined
    """
    try:
        result = run_command([uv_bin, "version", "--short"])
        version = result.stdout.strip()
        if not version:
            raise ValueError("Empty version string")
        return version
    except (subprocess.CalledProcessError, ValueError) as e:
        print_colored(Colors.RED, f"[ERROR] Could not determine version from pyproject.toml: {e}")
        sys.exit(1)


def get_current_branch() -> str:
    """Get the current git branch name.

    Returns:
        Branch name

    Raises:
        SystemExit: If branch cannot be determined
    """
    try:
        result = run_command(["git", "rev-parse", "--abbrev-ref", "HEAD"])
        branch = result.stdout.strip()
        if not branch:
            raise ValueError("Empty branch name")
        return branch
    except (subprocess.CalledProcessError, ValueError) as e:
        print_colored(Colors.RED, f"[ERROR] Could not determine current branch: {e}")
        sys.exit(1)


def get_default_branch() -> str:
    """Get the default branch from remote.

    Returns:
        Default branch name

    Raises:
        SystemExit: If default branch cannot be determined
    """
    try:
        result = run_command(["git", "remote", "show", "origin"])
        for line in result.stdout.splitlines():
            if "HEAD branch" in line:
                branch = line.split()[-1]
                if branch:
                    return branch
        raise ValueError("Could not parse default branch")
    except (subprocess.CalledProcessError, ValueError) as e:
        print_colored(Colors.RED, f"[ERROR] Could not determine default branch from remote: {e}")
        sys.exit(1)


def check_working_tree_clean() -> None:
    """Check if the working tree is clean.

    Raises:
        SystemExit: If there are uncommitted changes
    """
    result = run_command(["git", "status", "--porcelain"])
    if result.stdout.strip():
        print_colored(Colors.RED, "[ERROR] You have uncommitted changes:")
        run_command(["git", "status", "--short"], capture_output=False)
        print_colored(Colors.RED, "\n[ERROR] Please commit or stash your changes before releasing.")
        sys.exit(1)


def check_remote_status(current_branch: str) -> None:
    """Check if branch is in sync with remote.

    Args:
        current_branch: Name of the current branch

    Raises:
        SystemExit: If branch is behind remote or diverged
    """
    print_colored(Colors.BLUE, "[INFO] Checking remote status...")

    # Fetch latest changes from remote
    result = run_command(["git", "fetch", "origin"], capture_output=True, check=False)
    if result.returncode != 0:
        print_colored(Colors.YELLOW, "[WARN] Failed to fetch from remote. Continuing with local information.")
        # Continue anyway - the user might be offline or have auth issues but still want to proceed

    # Get upstream branch
    try:
        result = run_command(
            ["git", "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"],
            check=False,
        )
        if result.returncode != 0:
            print_colored(Colors.RED, f"[ERROR] No upstream branch configured for {current_branch}")
            sys.exit(1)
        upstream = result.stdout.strip()
    except subprocess.CalledProcessError:
        print_colored(Colors.RED, f"[ERROR] No upstream branch configured for {current_branch}")
        sys.exit(1)

    # Get commit hashes
    local_result = run_command(["git", "rev-parse", "@"])
    local = local_result.stdout.strip()

    remote_result = run_command(["git", "rev-parse", upstream])
    remote = remote_result.stdout.strip()

    base_result = run_command(["git", "merge-base", "@", upstream])
    base = base_result.stdout.strip()

    # Check sync status
    if local == remote:
        # Up to date
        return

    if local == base:
        # Local is behind remote
        print_colored(Colors.RED, f"[ERROR] Your branch is behind '{upstream}'. Please pull changes.")
        sys.exit(1)
    elif remote == base:
        # Local is ahead of remote
        print_colored(Colors.YELLOW, f"[WARN] Your branch is ahead of '{upstream}'.")
        print("Unpushed commits:")
        run_command(["git", "log", "--oneline", "--graph", "--decorate", f"{upstream}..HEAD"], capture_output=False)

        if prompt_continue("Push changes to remote before releasing?"):
            run_command(["git", "push", "origin", current_branch], capture_output=False)
    else:
        # Branches have diverged
        print_colored(Colors.RED, f"[ERROR] Your branch has diverged from '{upstream}'. Please reconcile.")
        sys.exit(1)


def check_tag_exists_locally(tag: str) -> bool:
    """Check if a tag exists locally.

    Args:
        tag: Tag name to check

    Returns:
        True if tag exists locally, False otherwise
    """
    result = run_command(["git", "rev-parse", tag], check=False, capture_output=True)
    return result.returncode == 0


def check_tag_exists_remotely(tag: str) -> bool:
    """Check if a tag exists on remote.

    Args:
        tag: Tag name to check

    Returns:
        True if tag exists on remote, False otherwise
    """
    result = run_command(
        ["git", "ls-remote", "--exit-code", "--tags", "origin", f"refs/tags/{tag}"],
        check=False,
        capture_output=True,
    )
    return result.returncode == 0


def is_gpg_signing_enabled() -> bool:
    """Check if GPG signing is configured for git.

    Returns:
        True if GPG signing is enabled, False otherwise
    """
    # Check if user.signingkey is set
    result = run_command(["git", "config", "--get", "user.signingkey"], check=False)
    if result.returncode == 0 and result.stdout.strip():
        return True

    # Check if commit.gpgsign is true
    result = run_command(["git", "config", "--get", "commit.gpgsign"], check=False)
    if result.returncode == 0 and result.stdout.strip() == "true":
        return True

    return False


def create_tag(tag: str) -> None:
    """Create a git tag.

    Args:
        tag: Tag name to create
    """
    if is_gpg_signing_enabled():
        print_colored(Colors.BLUE, "[INFO] GPG signing is enabled. Creating signed tag.")
        run_command(["git", "tag", "-s", tag, "-m", f"Release {tag}"], capture_output=False)
    else:
        print_colored(Colors.BLUE, "[INFO] GPG signing is not enabled. Creating unsigned tag.")
        run_command(["git", "tag", "-a", tag, "-m", f"Release {tag}"], capture_output=False)

    print_colored(Colors.GREEN, f"[SUCCESS] Tag '{tag}' created locally")


def push_tag(tag: str) -> None:
    """Push a tag to remote.

    Args:
        tag: Tag name to push
    """
    run_command(["git", "push", "origin", f"refs/tags/{tag}"], capture_output=False)


def get_repo_url() -> str:
    """Get the repository URL from git remote.

    Returns:
        Repository slug (e.g., "user/repo")
    """
    try:
        result = run_command(["git", "remote", "get-url", "origin"])
        url = result.stdout.strip()

        # Parse git@github.com:user/repo.git format
        if url.startswith("git@github.com:"):
            repo_path = url.replace("git@github.com:", "")
            if repo_path.endswith(".git"):
                repo_path = repo_path[:-4]
            return repo_path

        # Parse https://github.com/user/repo.git format
        if url.startswith("https://github.com/"):
            repo_path = url.replace("https://github.com/", "")
            if repo_path.endswith(".git"):
                repo_path = repo_path[:-4]
            return repo_path

        # For other URL formats, return the original URL
        return url
    except subprocess.CalledProcessError:
        return ""


def get_last_tag() -> str:
    """Get the last tag in the repository.

    Returns:
        Last tag name, or empty string if no tags exist
    """
    result = run_command(["git", "describe", "--tags", "--abbrev=0"], check=False)
    if result.returncode == 0:
        return result.stdout.strip()
    return ""


def count_commits_since_tag(last_tag: str, current_tag: str) -> int:
    """Count commits between two tags.

    Args:
        last_tag: Previous tag name
        current_tag: Current tag name

    Returns:
        Number of commits between tags
    """
    result = run_command(["git", "rev-list", f"{last_tag}..{current_tag}", "--count"], check=False)
    if result.returncode == 0:
        try:
            return int(result.stdout.strip())
        except ValueError:
            return 0
    return 0


def do_release(uv_bin: str) -> None:
    """Execute the release process.

    Args:
        uv_bin: Path to uv binary
    """
    # Get current version
    current_version = get_version(uv_bin)
    tag = f"v{current_version}"

    # Get current branch
    current_branch = get_current_branch()

    # Get default branch
    default_branch = get_default_branch()

    # Warn if not on default branch
    if current_branch != default_branch:
        print_colored(
            Colors.YELLOW,
            f"[WARN] You are on branch '{current_branch}' but the default branch is '{default_branch}'",
        )
        print_colored(Colors.YELLOW, "[WARN] Releases are typically created from the default branch.")
        if not prompt_continue(f"Proceed with release from '{current_branch}'?"):
            sys.exit(0)

    print_colored(Colors.BLUE, f"[INFO] Current version: {current_version}")
    print_colored(Colors.BLUE, f"[INFO] Tag to create: {tag}")

    # Check for uncommitted changes
    check_working_tree_clean()

    # Check remote status
    check_remote_status(current_branch)

    # Check if tag exists locally
    skip_tag_create = False
    if check_tag_exists_locally(tag):
        print_colored(Colors.YELLOW, f"[WARN] Tag '{tag}' already exists locally")
        if not prompt_continue("Tag exists. Skip tag creation and proceed to push?"):
            sys.exit(0)
        skip_tag_create = True

    # Check if tag exists on remote
    if check_tag_exists_remotely(tag):
        print_colored(Colors.RED, f"[ERROR] Tag '{tag}' already exists on remote")
        print(f"The release for version {current_version} has already been published.")
        sys.exit(1)

    # Step 1: Create the tag (if it doesn't exist)
    if not skip_tag_create:
        print_colored(Colors.BLUE, "\n=== Step 1: Create Tag ===")
        print(f"Creating tag '{tag}' for version {current_version}")
        if not prompt_continue(""):
            sys.exit(0)

        create_tag(tag)

    # Step 2: Push the tag to remote
    print_colored(Colors.BLUE, "\n=== Step 2: Push Tag to Remote ===")
    print(f"Pushing tag '{tag}' to origin will trigger the release workflow.")

    # Show commits since last tag
    last_tag = get_last_tag()
    if last_tag and last_tag != tag:
        commit_count = count_commits_since_tag(last_tag, tag)
        print(f"Commits since {last_tag}: {commit_count}")

    if not prompt_continue(""):
        sys.exit(0)

    # Push the tag
    push_tag(tag)

    # Show success message
    repo_url = get_repo_url()
    print_colored(Colors.GREEN, f"\n[SUCCESS] Release tag {tag} pushed to remote!")
    print_colored(Colors.BLUE, "[INFO] The release workflow will now be triggered automatically.")
    if repo_url:
        print_colored(Colors.BLUE, f"[INFO] Monitor progress at: https://github.com/{repo_url}/actions")


def main() -> None:
    """Main entry point for the release script."""
    parser = argparse.ArgumentParser(
        description="Create tag and push to remote (with prompts)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                    (create tag and push with prompts)
""",
    )
    parser.parse_args()

    # Check if pyproject.toml exists
    if not Path("pyproject.toml").exists():
        print_colored(Colors.RED, "[ERROR] pyproject.toml not found in current directory")
        sys.exit(1)

    # Check if uv is available
    uv_bin = os.environ.get("UV_BIN", "./bin/uv")
    uv_path = Path(uv_bin)
    if not uv_path.exists() or not os.access(uv_path, os.X_OK):
        print_colored(Colors.RED, f"[ERROR] uv not found at {uv_bin}. Run 'make install-uv' first.")
        sys.exit(1)

    # Execute release
    do_release(uv_bin)


if __name__ == "__main__":
    main()
