"""Install a locked private wheel using credentials exported across the setup boundary."""

from __future__ import annotations

import base64
import functools
import http.server
import os
import shutil
import subprocess  # nosec B404 - runs fixture setup and uv against a loopback index
import threading
import zipfile
from pathlib import Path

import pytest
import yaml

_ROOT = Path(__file__).resolve().parents[2]


def test_authenticated_setup_consumption(tmp_path):
    """Setup exports survive an empty legacy secret and enable frozen installation."""
    uv = shutil.which("uv")
    if not uv:
        pytest.skip("uv is required")
    index = tmp_path / "index"
    package = index / "simple/private-demo"
    package.mkdir(parents=True)
    wheel = package / "private_demo-1.0.0-py3-none-any.whl"
    with zipfile.ZipFile(wheel, "w") as archive:
        archive.writestr("private_demo/__init__.py", "VALUE = 1737\n")
        archive.writestr(
            "private_demo-1.0.0.dist-info/METADATA", "Metadata-Version: 2.1\nName: private-demo\nVersion: 1.0.0\n"
        )
        archive.writestr(
            "private_demo-1.0.0.dist-info/WHEEL", "Wheel-Version: 1.0\nRoot-Is-Purelib: true\nTag: py3-none-any\n"
        )
        archive.writestr("private_demo-1.0.0.dist-info/RECORD", "")
    (package / "index.html").write_text(f'<a href="{wheel.name}">{wheel.name}</a>')
    authorized = []

    class Handler(http.server.SimpleHTTPRequestHandler):
        """Require HTTP Basic authentication for every index and wheel request."""

        def do_GET(self):
            """Reject requests without the setup credential."""
            if self.headers.get("Authorization") != "Basic " + base64.b64encode(b"fixture:secret").decode():
                self.send_response(401)
                self.send_header("WWW-Authenticate", 'Basic realm="test"')
                self.end_headers()
                return
            authorized.append(self.path)
            super().do_GET()

        def log_message(self, *_args):
            """Keep routine loopback requests out of test output."""

    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(Handler, directory=str(index)))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        project = tmp_path / "consumer"
        project.mkdir()
        (project / "pyproject.toml").write_text(
            '[project]\nname="consumer"\nversion="0.1.0"\nrequires-python=">=3.11"\n'
            'dependencies=["private-demo==1.0.0"]\n'
        )
        url = f"http://fixture:secret@127.0.0.1:{server.server_port}/simple"
        hook = project / ".github/actions/rhiza-setup/action.yml"
        hook.parent.mkdir(parents=True)
        hook.write_text(
            yaml.safe_dump(
                {
                    "runs": {
                        "using": "composite",
                        "steps": [
                            {
                                "shell": "bash",
                                "run": 'printf "UV_EXTRA_INDEX_URL=%s\\n" "$TEST_INDEX" >> "$GITHUB_ENV"',
                            }
                        ],
                    }
                }
            )
        )
        dispatcher = yaml.safe_load((_ROOT / ".github/actions/rhiza-consumer-setup/action.yml").read_text())
        environment = {k: v for k, v in os.environ.items() if not k.startswith("UV_")}
        environment.update(
            ENABLED="true",
            EVENT_NAME="push",
            HEAD_REPOSITORY="",
            CALLER_REPOSITORY="acme/consumer",
            GITHUB_ENV=str(project / "github-env"),
            TEST_INDEX=url,
            UV_CACHE_DIR=str(tmp_path / "cache"),
            UV_PYTHON_DOWNLOADS="never",
        )

        def run(command, env):
            """Execute real setup and dependency commands with bounded runtimes."""
            return subprocess.run(
                command, cwd=project, env=env, capture_output=True, text=True, check=False, timeout=60
            )

        guard = run(["bash", "-e", "-c", dispatcher["runs"]["steps"][0]["run"]], environment)
        assert guard.returncode == 0, guard.stderr
        assert dispatcher["runs"]["steps"][1]["uses"] == "./.github/actions/rhiza-setup"
        setup = yaml.safe_load(hook.read_text())["runs"]["steps"][0]
        result = run(["bash", "-e", "-c", setup["run"]], environment)
        assert result.returncode == 0, result.stderr
        environment.update(line.split("=", 1) for line in Path(environment["GITHUB_ENV"]).read_text().splitlines())
        # The dependency-step expression preserves GITHUB_ENV when the legacy secret is empty.
        for workflow in ("ci", "book", "marimo", "benchmark", "weekly", "release"):
            definition = yaml.safe_load((_ROOT / f".github/workflows/rhiza_{workflow}.yml").read_text())
            for job in definition["jobs"].values():
                for step in job.get("steps", []):
                    value = step.get("env", {}).get("UV_EXTRA_INDEX_URL")
                    if value:
                        assert value == "${{ secrets.UV_EXTRA_INDEX_URL || env.UV_EXTRA_INDEX_URL }}"
        result = run([uv, "lock"], environment)
        assert result.returncode == 0, result.stderr
        lock = (project / "uv.lock").read_bytes()
        # No credentials: a fresh cache must fail, proving the index enforces auth.
        unauthenticated = {**environment, "UV_EXTRA_INDEX_URL": url.replace("fixture:secret@", "")}
        result = run([uv, "sync", "--frozen"], unauthenticated)
        assert result.returncode != 0
        result = run([uv, "sync", "--frozen"], environment)
        assert result.returncode == 0, result.stderr
        result = run(
            [uv, "run", "--frozen", "python", "-c", "import private_demo; assert private_demo.VALUE == 1737"],
            environment,
        )
        assert result.returncode == 0, result.stderr
        assert (project / "uv.lock").read_bytes() == lock
        assert any(path.endswith(".whl") for path in authorized)
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
