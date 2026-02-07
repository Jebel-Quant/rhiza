# Installation

Complete installation guide for Rhiza and its dependencies.

---

## System Requirements

### Operating System

Rhiza works on:

- **Linux** (Ubuntu, Debian, Fedora, etc.)
- **macOS** (10.15+)
- **Windows** via **WSL2 only** (native Windows not supported)

!!! warning "Windows Users"
    Rhiza uses POSIX shell scripts and requires WSL2 (Windows Subsystem for Linux 2). Native Windows is not supported.

### Python Version

!!! info "No System Python Required"
    While Rhiza creates projects targeting **Python 3.11+**, you **do not need Python pre-installed** on your system.
    
    The `uv` package manager handles Python installation automatically. Rhiza projects are tested against:
    
    - Python 3.11
    - Python 3.12
    - Python 3.13
    - Python 3.14
    
    `uv` will download and manage the appropriate Python version for your project.

---

## Installing Dependencies

### 1. Install Git

Git is the only system prerequisite:

=== "Ubuntu/Debian"
    ```bash
    sudo apt install git
    ```

=== "macOS"
    ```bash
    brew install git
    ```

=== "WSL2"
    ```bash
    sudo apt install git
    ```

### 2. uv (Auto-Installed)

!!! success "No Manual Installation Needed"
    You **do not need to install `uv` manually**. Rhiza automatically installs it to `./bin/` in your project when you run `make install`.

However, if you want to use `uvx` commands directly, you can optionally install `uv` globally:

=== "Linux/macOS/WSL2"
    ```bash
    curl -LsSf https://astral.sh/uv/install.sh | sh
    ```

=== "Using pip"
    ```bash
    pip install uv
    ```

!!! info "How uv Works"
    `uv` is a blazing-fast Python package installer written in Rust. It:
    
    - **Installs Python automatically** - No system Python needed
    - **10-100x faster** than pip
    - **Better dependency resolution**
    - **Self-contained** - Installs to project's `./bin/` directory
    
    Learn more: [uv documentation](https://docs.astral.sh/uv/)

---

## Installing Rhiza

### Option 1: Using make install (Recommended)

The fully self-contained approach - **no prerequisites needed**:

```bash
git clone https://github.com/jebel-quant/rhiza.git
cd rhiza
make install
```

This automatically:
1. **Installs `uv`** to `./bin/` (if not in PATH)
2. **Downloads Python** (via uv, if needed)
3. **Creates virtual environment** in `.venv`
4. **Installs all dependencies**
5. **Installs Rhiza** in development mode

!!! success "Self-Contained"
    Everything is installed at the repository level in `./bin/` and `.venv/`. No system-wide changes.

### Option 2: Using uvx (Quick Testing)

Run Rhiza without cloning the repository:

```bash
uvx rhiza --help
```

This downloads and runs Rhiza in an isolated environment. Useful for trying out Rhiza before committing.

### Option 3: Using uv (Manual)

If you prefer manual control:

```bash
git clone https://github.com/jebel-quant/rhiza.git
cd rhiza
uv venv
source .venv/bin/activate
uv pip install -e .
```

---

## Verifying Installation

After running `make install`, verify the setup:

```bash
# Check that uv was installed
./bin/uv --version

# Activate the virtual environment
source .venv/bin/activate

# Check Python version (managed by uv)
python --version  # Should be 3.11+

# Check Rhiza installation
python -m rhiza --version
```

Expected output:
```
uv 0.x.x
Python 3.11.x (or higher)
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

### Python version issues

If you encounter Python version errors:

```bash
# Let uv install the correct Python version
make install

# Or specify a version explicitly
uv venv --python 3.12
```

!!! tip "uv manages Python"
    You don't need to install Python manually. `uv` will automatically download the required version.

### uv command not found

Ensure `uv` is in your PATH:

```bash
# Add to ~/.bashrc or ~/.zshrc
export PATH="$HOME/.cargo/bin:$PATH"

# Reload shell
source ~/.bashrc  # or ~/.zshrc
```

### Permission errors

Rhiza installs everything locally to `./bin/` and `.venv/` - no `sudo` needed:

```bash
# Ensure you have write permissions in the project directory
ls -la

# If needed, fix permissions
chmod +w .

# Then run install
make install
```

!!! success "No sudo Required"
    Rhiza is designed to be self-contained. All installations happen in your project directory.

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
