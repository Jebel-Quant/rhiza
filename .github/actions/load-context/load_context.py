"""Load environment variables and secrets from a manifest file."""

import json
import os
import sys


def main():
    """Docstring for main."""
    manifest_path = os.environ.get("INPUT_MANIFEST")
    secrets_context_json = os.environ.get("INPUT_SECRETS_CONTEXT", "{}")
    strict_mode = os.environ.get("INPUT_STRICT", "false").lower() == "true"

    if not manifest_path:
        print("::error::Manifest path not provided.")
        sys.exit(1)

    if not os.path.exists(manifest_path):
        print(f"::error::Manifest file not found at {manifest_path}")
        sys.exit(1)

    # Simple JSON loading. If YAML is needed, it would require PyYAML.
    # We will try to load as JSON.
    try:
        with open(manifest_path) as f:
            manifest = json.load(f)
    except json.JSONDecodeError as e:
        print(f"::error::Failed to parse manifest as JSON: {e}")
        # Could optionally try YAML here if PyYAML was guaranteed
        sys.exit(1)

    env_vars = manifest.get("env", {})
    secrets_to_pull = manifest.get("secrets", [])  # List of secret names or dict mapping

    github_env = os.environ.get("GITHUB_ENV")
    if not github_env:
        print("::error::GITHUB_ENV not defined.")
        sys.exit(1)

    # Handle Env Vars
    with open(github_env, "a") as f:
        for key, value in env_vars.items():
            print(f"Setting env var: {key}")
            # Handle multi-line support
            if "\n" in str(value):
                delimiter = "EOF"
                f.write(f"{key}<<{delimiter}\n{value}\n{delimiter}\n")
            else:
                f.write(f"{key}={value}\n")

    # Handle Secrets
    # The secrets_context is passed as a JSON string
    try:
        secrets = json.loads(secrets_context_json)
    except json.JSONDecodeError:
        print("::warning::Could not parse secrets context.")
        secrets = {}

    if secrets_to_pull:
        with open(github_env, "a") as f:
            # If it's a list, map NAME -> NAME
            if isinstance(secrets_to_pull, list):
                for secret_name in secrets_to_pull:
                    val = secrets.get(secret_name)
                    if val:
                        print(f"Loading secret: {secret_name}")
                        print(f"::add-mask::{val}")
                        f.write(f"{secret_name}={val}\n")
                    else:
                        msg = f"Secret {secret_name} not found in secrets context."
                        if strict_mode:
                            print(f"::error::{msg}")
                            sys.exit(1)
                        else:
                            print(f"::warning::{msg}")

            # If it's a dict, map ENV_VAR -> SECRET_NAME
            elif isinstance(secrets_to_pull, dict):
                for env_name, secret_name in secrets_to_pull.items():
                    val = secrets.get(secret_name)
                    if val:
                        print(f"Loading secret {secret_name} as {env_name}")
                        print(f"::add-mask::{val}")
                        f.write(f"{env_name}={val}\n")
                    else:
                        msg = f"Secret {secret_name} not found in secrets context."
                        if strict_mode:
                            print(f"::error::{msg}")
                            sys.exit(1)
                        else:
                            print(f"::warning::{msg}")


if __name__ == "__main__":
    main()
