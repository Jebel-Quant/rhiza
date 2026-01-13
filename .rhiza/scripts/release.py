#!/usr/bin/env python3
"""Release script for creating and pushing git tags.

This script:
- Creates a git tag based on the current version in pyproject.toml
- Pushes the tag to remote to trigger the release workflow
- Performs checks (branch, upstream status, clean working tree)
"""

import os
import subprocess
import sys
from pathlib import Path

import typer
from loguru import logger

# Configure loguru logger
logger.remove()  # Remove default handler
logger.add(
    sys.stdout,
    format="<level>{message}</level>",
    level="INFO",
    colorize=True,
)


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
        message: Message to display to user

    Returns:
        True if user wants to continue, False otherwise
    """
    if message:
        prompt_text = f"[PROMPT] {message} Continue? [y/N] "
    else:
        prompt_text = "[PROMPT] Continue? [y/N] "
    print()  # Print newline before prompt
    logger.warning(prompt_text)
    answer = input().strip().lower()
    if answer in ("y", "yes"):
        return True
    logger.info("Aborted by user")
    return False


def get_version(uv_bin: str) -> str:
    """Get the current version from pyproject.toml using uv.

    Args:
        uv_bin: Path to uv binary

    Returns:
        Version string

    Raises:
        typer.Exit: If version cannot be determined
    """
    try:
        result = run_command([uv_bin, "version", "--short"])
        version = result.stdout.strip()
        if not version:
            raise ValueError("Empty version string")
        return version
    except (subprocess.CalledProcessError, ValueError) as e:
        logger.error(f"Could not determine version from pyproject.toml: {e}")
        raise typer.Exit(1)


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
        logger.error(f"Could not determine current branch: {e}")
        raise typer.Exit(1)


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
        logger.error(f"Could not determine default branch from remote: {e}")
        raise typer.Exit(1)


def check_working_tree_clean() -> None:
    """Check if the working tree is clean.

    Raises:
        SystemExit: If there are uncommitted changes
    """
    result = run_command(["git", "status", "--porcelain"])
    if result.stdout.strip():
        logger.error("You have uncommitted changes:")
        run_command(["git", "status", "--short"], capture_output=False)
        logger.error("\n[ERROR] Please commit or stash your changes before releasing.")
        raise typer.Exit(1)


def check_remote_status(current_branch: str) -> None:
    """Check if branch is in sync with remote.

    Args:
        current_branch: Name of the current branch

    Raises:
        SystemExit: If branch is behind remote or diverged
    """
    logger.info("Checking remote status...")

    # Fetch latest changes from remote
    result = run_command(["git", "fetch", "origin"], capture_output=True, check=False)
    if result.returncode != 0:
        logger.warning("Failed to fetch from remote. Continuing with local information.")
        # Continue anyway - the user might be offline or have auth issues but still want to proceed

    # Get upstream branch
    try:
        result = run_command(
            ["git", "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"],
            check=False,
        )
        if result.returncode != 0:
            logger.error(f"No upstream branch configured for {current_branch}")
            raise typer.Exit(1)
        upstream = result.stdout.strip()
    except subprocess.CalledProcessError:
        logger.error(f"No upstream branch configured for {current_branch}")
        raise typer.Exit(1)

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
        logger.error(f"Your branch is behind '{upstream}'. Please pull changes.")
        raise typer.Exit(1)
    elif remote == base:
        # Local is ahead of remote
        logger.warning(f"Your branch is ahead of '{upstream}'.")
        print("Unpushed commits:")
        run_command(["git", "log", "--oneline", "--graph", "--decorate", f"{upstream}..HEAD"], capture_output=False)

        if prompt_continue("Push changes to remote before releasing?"):
            run_command(["git", "push", "origin", current_branch], capture_output=False)
    else:
        # Branches have diverged
        logger.error(f"Your branch has diverged from '{upstream}'. Please reconcile.")
        raise typer.Exit(1)


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
        logger.info("GPG signing is enabled. Creating signed tag.")
        run_command(["git", "tag", "-s", tag, "-m", f"Release {tag}"], capture_output=False)
    else:
        logger.info("GPG signing is not enabled. Creating unsigned tag.")
        run_command(["git", "tag", "-a", tag, "-m", f"Release {tag}"], capture_output=False)

    logger.success(f"Tag '{tag}' created locally")


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


def count_commits_since_tag(last_tag: str, current_ref: str) -> int:
    """Count commits between a tag and a git reference.

    Args:
        last_tag: Previous tag name
        current_ref: Git reference (commit hash, branch, HEAD, tag, etc.)

    Returns:
        Number of commits between references
    """
    result = run_command(["git", "rev-list", f"{last_tag}..{current_ref}", "--count"], check=False)
    if result.returncode == 0:
        try:
            return int(result.stdout.strip())
        except ValueError:
            return 0
    return 0


def _validate_branch(current_branch: str, default_branch: str, dry_run: bool) -> None:
    """Validate that release is from the correct branch.

    Args:
        current_branch: Current git branch
        default_branch: Default branch for the repository
        dry_run: Whether this is a dry run
    """
    if current_branch != default_branch:
        logger.warning(f"You are on branch '{current_branch}' but the default branch is '{default_branch}'")
        logger.warning("Releases are typically created from the default branch.")
        if not dry_run and not prompt_continue(f"Proceed with release from '{current_branch}'?"):
            raise typer.Exit(0)


def _check_tag_status(tag: str, current_version: str, dry_run: bool) -> bool:
    """Check if tag exists and determine if creation should be skipped.

    Args:
        tag: Tag name to check
        current_version: Current version from pyproject.toml
        dry_run: Whether this is a dry run

    Returns:
        True if tag creation should be skipped, False otherwise
    """
    skip_tag_create = False
    if check_tag_exists_locally(tag):
        logger.warning(f"Tag '{tag}' already exists locally")
        if not dry_run and not prompt_continue("Tag exists. Skip tag creation and proceed to push?"):
            raise typer.Exit(0)
        skip_tag_create = True

    if check_tag_exists_remotely(tag):
        logger.error(f"Tag '{tag}' already exists on remote")
        print(f"The release for version {current_version} has already been published.")
        raise typer.Exit(1)

    return skip_tag_create


def _create_tag_step(tag: str, current_version: str, skip_tag_create: bool, dry_run: bool) -> None:
    """Execute tag creation step.

    Args:
        tag: Tag name to create
        current_version: Current version from pyproject.toml
        skip_tag_create: Whether to skip tag creation
        dry_run: Whether this is a dry run
    """
    if skip_tag_create:
        return

    logger.info("\n=== Step 1: Create Tag ===")
    if dry_run:
        logger.warning(f"[DRY RUN] Would create tag '{tag}' for version {current_version}")
    else:
        print(f"Creating tag '{tag}' for version {current_version}")
        if not prompt_continue(""):
            raise typer.Exit(0)
        create_tag(tag)


def _push_tag_step(tag: str, dry_run: bool) -> None:
    """Execute tag push step.

    Args:
        tag: Tag name to push
        dry_run: Whether this is a dry run
    """
    logger.info("\n=== Step 2: Push Tag to Remote ===")
    if dry_run:
        logger.warning(f"[DRY RUN] Would push tag '{tag}' to origin")
    else:
        print(f"Pushing tag '{tag}' to origin will trigger the release workflow.")

    # Show commits since last tag
    last_tag = get_last_tag()
    if last_tag and last_tag != tag:
        commit_count = count_commits_since_tag(last_tag, "HEAD")
        print(f"Commits since {last_tag}: {commit_count}")

    if dry_run:
        _show_dry_run_summary(tag)
    else:
        if not prompt_continue(""):
            raise typer.Exit(0)
        push_tag(tag)
        _show_success_message(tag)


def _show_dry_run_summary(tag: str) -> None:
    """Show dry-run summary message.

    Args:
        tag: Tag that would be created
    """
    logger.success(f"[DRY RUN] Would have created and pushed release tag {tag}")
    repo_url = get_repo_url()
    if repo_url:
        logger.info(f"Release workflow would be triggered at: https://github.com/{repo_url}/actions")


def _show_success_message(tag: str) -> None:
    """Show success message after pushing tag.

    Args:
        tag: Tag that was pushed
    """
    repo_url = get_repo_url()
    logger.success(f"\n[SUCCESS] Release tag {tag} pushed to remote!")
    logger.info("The release workflow will now be triggered automatically.")
    if repo_url:
        logger.info(f"Monitor progress at: https://github.com/{repo_url}/actions")


def do_release(uv_bin: str, dry_run: bool = False) -> None:
    """Execute the release process.

    Args:
        uv_bin: Path to uv binary
        dry_run: If True, show what would happen without making changes
    """
    # Get version and tag info
    current_version = get_version(uv_bin)
    tag = f"v{current_version}"

    if dry_run:
        logger.warning("[DRY RUN] No changes will be made")

    # Get branch information
    current_branch = get_current_branch()
    default_branch = get_default_branch()

    # Validate branch
    _validate_branch(current_branch, default_branch, dry_run)

    logger.info(f"Current version: {current_version}")
    logger.info(f"Tag to create: {tag}")

    # Perform validation checks
    check_working_tree_clean()
    check_remote_status(current_branch)

    # Check tag status
    skip_tag_create = _check_tag_status(tag, current_version, dry_run)

    # Execute release steps
    _create_tag_step(tag, current_version, skip_tag_create, dry_run)
    _push_tag_step(tag, dry_run)


app = typer.Typer()


@app.command()
def main(
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        "-n",
        help="Show what would happen without making any changes",
    ),
) -> None:
    """Create tag and push to remote (with prompts).

    Example:
        release.py                    (create tag and push with prompts)
        release.py --dry-run          (show what would happen)
    """
    # Check if pyproject.toml exists
    if not Path("pyproject.toml").exists():
        logger.error("pyproject.toml not found in current directory")
        raise typer.Exit(1)

    # Check if uv is available
    uv_bin = os.environ.get("UV_BIN", "./bin/uv")
    uv_path = Path(uv_bin)
    if not uv_path.exists() or not os.access(uv_path, os.X_OK):
        logger.error(f"uv not found at {uv_bin}. Run 'make install-uv' first.")
        raise typer.Exit(1)

    # Execute release
    do_release(uv_bin, dry_run=dry_run)


if __name__ == "__main__":
    app()
