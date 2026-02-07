# Installation

Complete installation guide for Rhiza and its dependencies.

---

## System Requirements

### Operating System

Rhiza works on:

- **Linux** (Ubuntu, Debian, Fedora, etc.)
- **macOS** (10.15+)
- **Windows** (with WSL2 recommended)

### Python Version

!!! info "Python Version Support"
    Rhiza requires **Python 3.11 or higher**. We test against:
    
    - Python 3.11
    - Python 3.12
    - Python 3.13
    - Python 3.14

---

## Installing Dependencies

### 1. Install Python

=== "Ubuntu/Debian"
    ```bash
    sudo apt update
    sudo apt install python3.11 python3-pip python3-venv
    ```

=== "macOS"
    ```bash
    # Using Homebrew
    brew install python@3.11
    ```

=== "Windows (WSL2)"
    ```bash
    sudo apt update
    sudo apt install python3.11 python3-pip python3-venv
    ```

=== "From source"
    ```bash
    # Using pyenv
    curl https://pyenv.run | bash
    pyenv install 3.11
    pyenv global 3.11
    ```

### 2. Install uv (Recommended)

`uv` is a blazing-fast Python package installer and resolver, written in Rust.

=== "Linux/macOS"
    ```bash
    curl -LsSf https://astral.sh/uv/install.sh | sh
    ```

=== "Windows (PowerShell)"
    ```powershell
    powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
    ```

=== "Using pip"
    ```bash
    pip install uv
    ```

!!! tip "Why uv?"
    `uv` is **10-100x faster** than pip and provides better dependency resolution. It's the recommended way to manage Python packages in 2026.

### 3. Install Git

=== "Ubuntu/Debian"
    ```bash
    sudo apt install git
    ```

=== "macOS"
    ```bash
    brew install git
    ```

=== "Windows"
    Download from [git-scm.com](https://git-scm.com/download/win)

---

## Installing Rhiza

### Option 1: Using uvx (Recommended)

Run Rhiza without installing it globally:

```bash
uvx rhiza --help
```

This downloads and runs Rhiza in an isolated environment.

### Option 2: Using uv

Install Rhiza into a virtual environment:

```bash
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install rhiza
```

### Option 3: Using pip

Traditional pip installation:

```bash
pip install rhiza
```

### Option 4: From Source

For development or to use the latest features:

```bash
git clone https://github.com/jebel-quant/rhiza.git
cd rhiza
make install
```

This will:
1. Install `uv` if not already installed
2. Create a virtual environment in `.venv`
3. Install all dependencies
4. Install Rhiza in development mode

---

## Verifying Installation

Check that everything is installed correctly:

```bash
# Check Python version
python --version  # Should be 3.11+

# Check uv
uv --version

# Check Rhiza
uvx rhiza --version
```

Expected output:
```
Python 3.11.x
uv 0.x.x
rhiza 0.7.x
```

---

## Setting Up Your First Project

Now that Rhiza is installed, you can initialize a project:

### New Project

```bash
mkdir my-project
cd my-project
uvx rhiza init
```

This creates `.rhiza/template.yml` with default configuration.

### Existing Project

```bash
cd /path/to/existing/project
uvx rhiza init
```

Rhiza detects existing files and suggests appropriate configuration.

---

## Optional: Development Tools

For the best experience, install these optional tools:

### Pre-commit

Automatically run code quality checks before commits:

```bash
uv pip install pre-commit
pre-commit install
```

### Make

Most Rhiza projects include a `Makefile` for common tasks:

=== "Ubuntu/Debian"
    ```bash
    sudo apt install build-essential
    ```

=== "macOS"
    ```bash
    xcode-select --install
    ```

### Docker (Optional)

For containerized development:

=== "Ubuntu/Debian"
    ```bash
    curl -fsSL https://get.docker.com | sh
    sudo usermod -aG docker $USER
    ```

=== "macOS"
    Download [Docker Desktop](https://www.docker.com/products/docker-desktop)

=== "Windows"
    Download [Docker Desktop](https://www.docker.com/products/docker-desktop)

---

## Configuration

### Environment Variables

You can configure Rhiza behavior with environment variables:

```bash
# Set custom template repository
export RHIZA_TEMPLATE_REPO="https://github.com/your-org/your-templates.git"

# Set custom cache directory
export RHIZA_CACHE_DIR="$HOME/.cache/rhiza"
```

Add these to your shell profile (`.bashrc`, `.zshrc`, etc.) to make them permanent.

### Configuration File

Create `~/.config/rhiza/config.yml` for global settings:

```yaml
template:
  default_repo: https://github.com/jebel-quant/rhiza.git
  default_ref: main

cache:
  directory: ~/.cache/rhiza
  ttl: 3600

logging:
  level: INFO
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
```

---

## Upgrading Rhiza

### Using uvx

`uvx` always uses the latest version by default. To force an upgrade:

```bash
uvx --refresh rhiza --version
```

### Using uv/pip

```bash
uv pip install --upgrade rhiza
# or
pip install --upgrade rhiza
```

### From Source

```bash
cd /path/to/rhiza
git pull
make install
```

---

## Troubleshooting

### Python version too old

If you get an error about Python version:

```bash
# Check current version
python --version

# Install newer version (using pyenv)
pyenv install 3.11
pyenv global 3.11
```

### uv command not found

Ensure `uv` is in your PATH:

```bash
# Add to ~/.bashrc or ~/.zshrc
export PATH="$HOME/.cargo/bin:$PATH"

# Reload shell
source ~/.bashrc  # or ~/.zshrc
```

### Permission errors

On Linux/macOS, you might need to use `sudo` or install to user directory:

```bash
# Install to user directory
pip install --user rhiza

# Or use virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate
pip install rhiza
```

### SSL certificate errors

If you encounter SSL errors:

```bash
# Update certificates (Ubuntu/Debian)
sudo apt install ca-certificates
sudo update-ca-certificates

# macOS
pip install --upgrade certifi
```

---

## Next Steps

!!! success "Installation Complete!"
    You're ready to start using Rhiza.

Continue to the [Quick Start](quickstart.md) guide to create your first project.

<div class="grid cards" markdown>

- :material-rocket: [**Quick Start**](quickstart.md)
    
    Get up and running in 5 minutes

- :material-sync: [**Your First Sync**](first-sync.md)
    
    Learn how to sync templates

- :material-book: [**Workflows**](../WORKFLOWS.md)
    
    Discover development workflows

</div>
