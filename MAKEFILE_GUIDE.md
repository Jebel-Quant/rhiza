# Makefile Guide for Rhiza

This guide explains how the Makefile system works in this repository and how to use it effectively.

## Table of Contents
1. [What is a Makefile?](#what-is-a-makefile)
2. [Repository Structure](#repository-structure)
3. [How to Use the Makefiles](#how-to-use-the-makefiles)
4. [Main Makefile Targets](#main-makefile-targets)
5. [Understanding the Makefile Hierarchy](#understanding-the-makefile-hierarchy)
6. [Common Workflows](#common-workflows)
7. [Troubleshooting](#troubleshooting)

---

## What is a Makefile?

A **Makefile** is a configuration file used by the `make` tool to automate tasks. It contains:
- **Targets**: Named tasks you can run (e.g., `install`, `test`, `clean`)
- **Dependencies**: Other targets that must run first
- **Commands**: Shell commands that execute when you run a target

### Basic Syntax

```makefile
target: dependencies
	command1
	command2
```

**Important**: Commands must be indented with a **TAB** (not spaces).

### Example

```makefile
hello:
	echo "Hello, World!"
```

Run with: `make hello`

---

## Repository Structure

This repository uses a **hierarchical Makefile structure** to organize tasks by domain:

```
rhiza/
├── Makefile                           # Main Makefile (orchestrates everything)
├── tests/Makefile.tests              # Testing-related targets
├── book/Makefile.book                # Documentation and book generation
└── presentation/Makefile.presentation # Presentation generation
```

### Why Multiple Makefiles?

- **Organization**: Each domain (testing, docs, presentations) has its own file
- **Maintainability**: Easier to find and update specific tasks
- **Modularity**: Can include/exclude modules as needed

---

## How to Use the Makefiles

### View Available Commands

```bash
make help
```

This displays all available targets organized by category:
- Bootstrap: Installation tasks
- Tools: Development tools
- Quality and Formatting: Code quality checks
- Releasing and Versioning: Version management
- Development and Testing: Tests and benchmarks
- Documentation: API docs and books
- Presentation: Slide generation

### Run a Target

```bash
make <target-name>
```

Examples:
```bash
make install      # Install dependencies
make test        # Run tests
make docs        # Generate documentation
make clean       # Clean build artifacts
```

### Common Options

- `make` (no target): Runs the default target (usually `help`)
- `make -n <target>`: Show commands without executing (dry run)
- `make -B <target>`: Force rebuild even if target exists

---

## Main Makefile Targets

### Bootstrap Targets

#### `make install-uv`
- Installs the `uv` package manager in `./bin/`
- **Use when**: Setting up the project for the first time
- **Example**: `make install-uv`

#### `make install`
- Installs `uv`, runs custom build scripts, creates virtual environment, installs dependencies
- **Use when**: First time setup or after pulling new changes
- **Example**: `make install`

#### `make clean`
- Removes build artifacts, caches, and local branches without remotes
- **Use when**: You want a fresh start or before making a release
- **Example**: `make clean`

### Development Targets

#### `make test`
- Runs all tests with coverage reports
- **Use when**: After making code changes
- **Output**: HTML coverage report in `_tests/html-coverage/`
- **Example**: `make test`

#### `make benchmark`
- Runs performance benchmarks
- **Use when**: Testing performance optimizations
- **Example**: `make benchmark`

#### `make marimo`
- Starts the Marimo notebook server
- **Use when**: Working with interactive notebooks
- **Example**: `make marimo`

### Quality and Formatting Targets

#### `make fmt`
- Runs pre-commit hooks and linting
- **Use when**: Before committing code
- **Example**: `make fmt`

#### `make deptry`
- Checks for unused dependencies
- **Use when**: Cleaning up dependencies
- **Example**: `make deptry`

### Documentation Targets

#### `make docs`
- Generates API documentation using `pdoc`
- **Output**: HTML documentation in `_pdoc/`
- **Example**: `make docs`

#### `make marimushka`
- Exports Marimo notebooks to HTML
- **Example**: `make marimushka`

#### `make book`
- Compiles the full companion book (runs tests, docs, marimushka)
- **Output**: Book in `_book/`
- **Example**: `make book`

### Presentation Targets

#### `make presentation`
- Generates HTML slides from `PRESENTATION.md`
- **Requirements**: Marp CLI (installs automatically if npm is available)
- **Output**: `presentation.html`
- **Example**: `make presentation`

#### `make presentation-pdf`
- Generates PDF slides from `PRESENTATION.md`
- **Output**: `presentation.pdf`
- **Example**: `make presentation-pdf`

#### `make presentation-serve`
- Serves presentation with live reload
- **Example**: `make presentation-serve`

### Release Targets

#### `make bump`
- Bumps the version number
- **Use when**: Preparing a new release
- **Example**: `make bump`

#### `make release`
- Creates a git tag and pushes to remote
- **Use when**: Publishing a new version
- **Example**: `make release`

#### `make post-release`
- Runs post-release tasks (if customization script exists)
- **Example**: `make post-release`

### Utility Targets

#### `make sync`
- Syncs with template repository
- **Use when**: Updating from the template
- **Example**: `make sync`

#### `make update-readme`
- Updates README.md with current Makefile help
- **Example**: `make update-readme`

#### `make customisations`
- Lists available custom scripts
- **Example**: `make customisations`

---

## Understanding the Makefile Hierarchy

### Main Makefile (`./Makefile`)

The main Makefile:
1. Defines common variables (colors, paths, etc.)
2. Sets the default target to `help`
3. **Includes** the sub-Makefiles using:
   ```makefile
   -include tests/Makefile.tests
   -include book/Makefile.book
   -include presentation/Makefile.presentation
   ```
4. Defines core targets (install, clean, fmt, etc.)

### The `-include` Directive

```makefile
-include tests/Makefile.tests
```

- Loads targets from another Makefile
- The `-` prefix means "don't fail if file doesn't exist"
- All included targets can access variables from the main Makefile

### Sub-Makefiles

#### `tests/Makefile.tests`
Adds:
- `test`: Run tests with coverage
- `benchmark`: Run performance tests

#### `book/Makefile.book`
Adds:
- `docs`: Generate API documentation
- `marimushka`: Export notebooks
- `book`: Compile full book

#### `presentation/Makefile.presentation`
Adds:
- `presentation`: Generate HTML slides
- `presentation-pdf`: Generate PDF slides
- `presentation-serve`: Serve with live reload

### How Targets Override

The main Makefile includes default fallback implementations for targets that are defined in sub-Makefiles:
```makefile
book docs marimushka test presentation presentation-pdf presentation-serve::
	@echo "error: '$@' not implemented in this environment" >&2
	@exit 1
```

This creates **default fallback implementations**. The `::` (double colon) syntax allows multiple rules for the same target. When sub-Makefiles are included, their versions override these defaults.

---

## Common Workflows

### First-Time Setup

```bash
# 1. Install uv and dependencies
make install

# 2. Verify installation
make help

# 3. Run tests to ensure everything works
make test
```

### Daily Development

```bash
# 1. Pull latest changes
git pull

# 2. Update dependencies (if needed)
make install

# 3. Make your code changes
# ... edit files ...

# 4. Format and lint
make fmt

# 5. Run tests
make test

# 6. Commit your changes
git add .
git commit -m "Your message"
```

### Before Committing

```bash
# Format code
make fmt

# Run tests
make test

# Check dependencies
make deptry
```

### Building Documentation

```bash
# Generate API docs
make docs

# Export notebooks
make marimushka

# Build complete book
make book

# View documentation
open _book/index.html  # or your browser
```

### Creating a Release

```bash
# 1. Ensure everything is clean and tested
make clean
make install
make test

# 2. Update version
make bump

# 3. Create release
make release

# 4. Run post-release tasks
make post-release
```

### Creating a Presentation

```bash
# Edit PRESENTATION.md
# ... make your changes ...

# Generate HTML slides
make presentation

# Or generate PDF
make presentation-pdf

# Or serve with live reload
make presentation-serve
```

---

## Troubleshooting

### "make: command not found"

**Problem**: `make` is not installed.

**Solution**: Install make:
- **Ubuntu/Debian**: `sudo apt-get install build-essential`
- **macOS**: `xcode-select --install`
- **Windows**: 
  - Option 1: Install [WSL (Windows Subsystem for Linux)](https://docs.microsoft.com/en-us/windows/wsl/install) and then use the Ubuntu instructions
  - Option 2: Install via [Chocolatey](https://chocolatey.org/): `choco install make`
  - Option 3: Use [Git Bash](https://gitforwindows.org/) which includes make

### "No rule to make target"

**Problem**: Target doesn't exist.

**Solution**: 
1. Run `make help` to see available targets
2. Check spelling of target name
3. Ensure sub-Makefiles exist if using modular targets

### "recipe commences before first target"

**Problem**: Indentation is wrong (spaces instead of tabs).

**Solution**: If editing Makefiles, ensure commands use TAB characters, not spaces.

### "uv: command not found"

**Problem**: `uv` is not installed or not in PATH.

**Solution**: Run `make install-uv` first, or check that `./bin/uv` exists.

### Tests/Docs Not Found

**Problem**: Sub-Makefile targets show warnings.

**Solution**: 
- Ensure directory structure matches expectations
- Check that `src/`, `tests/`, `book/` folders exist
- Some targets are optional and will skip gracefully

### Permission Denied

**Problem**: Scripts in `.github/scripts/` are not executable.

**Solution**: Make scripts executable:
```bash
chmod +x .github/scripts/*.sh
chmod +x .github/scripts/customisations/*.sh
```

---

## Advanced Features

### Debug Variables

Print any Makefile variable:
```bash
make print-UV_BIN
make print-SOURCE_FOLDER
```

### Run Custom Scripts

Place scripts in `.github/scripts/customisations/` and run:
```bash
make custom-scriptname
```

List available scripts:
```bash
make customisations
```

### Environment Variables

The Makefile sets:
- `UV_NO_MODIFY_PATH=1`: Prevents uv from modifying PATH
- `UV_VENV_CLEAR=1`: Clears venv before installation

You can override variables:
```bash
make install-uv UV_INSTALL_DIR=/custom/path
```

---

## Summary

The Makefile system in this repository:
1. **Main Makefile**: Orchestrates common tasks and includes sub-Makefiles
2. **Sub-Makefiles**: Organize domain-specific targets (tests, docs, presentations)
3. **Modular**: Each module can work independently
4. **User-Friendly**: Clear help system with `make help`
5. **Extensible**: Easy to add custom scripts and targets

### Key Commands to Remember

```bash
make help           # Show all available commands
make install        # Set up the project
make test           # Run tests
make fmt            # Format code
make docs           # Generate documentation
make clean          # Clean up
```

For more help, check the inline comments in each Makefile or run `make help`.
