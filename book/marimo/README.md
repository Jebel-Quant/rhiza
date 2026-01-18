# Marimo Notebooks

This directory contains interactive [Marimo](https://marimo.io/) notebooks for the Rhiza project.

## Available Notebooks

### 📊 rhiza.py - Marimo Feature Showcase

A comprehensive demonstration of Marimo's most useful features, including:

- **Interactive UI Elements**: Sliders, dropdowns, text inputs, checkboxes, and multiselect
- **Reactive Programming**: Automatic cell updates when dependencies change
- **Data Visualisation**: Interactive plots using Plotly
- **DataFrames**: Working with Pandas data
- **Layout Components**: Columns, tabs, and accordions for organised content
- **Forms**: Dictionary-based forms for collecting user input
- **Rich Text**: Markdown and LaTeX support for documentation
- **Advanced Features**: Callouts, collapsible accordions, and more

This notebook is perfect for:
- Learning Marimo's capabilities
- Understanding reactive programming in notebooks
- Seeing real examples of interactive UI components
- Getting started with Marimo in your own projects

## Running the Notebooks

### Using the Makefile

From the repository root:

```bash
make marimo
```

This will start the Marimo server and open all notebooks in the `book/marimo` directory.

### Running a Specific Notebook

To run a single notebook:

```bash
marimo edit book/marimo/rhiza.py
```

### Using uv (Recommended)

The notebooks include inline dependency metadata, making them self-contained:

```bash
uv run book/marimo/rhiza.py
```

This will automatically install the required dependencies and run the notebook.

## Notebook Structure

Marimo notebooks are **pure Python files** (`.py`), not JSON. This means:

- ✅ Easy version control with Git
- ✅ Standard code review workflows  
- ✅ No hidden metadata
- ✅ Compatible with all Python tools

Each notebook includes inline metadata that specifies its dependencies:

```python
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "marimo==0.18.4",
#     "numpy>=1.24.0",
# ]
# ///
```

## Configuration

Marimo is configured in `pyproject.toml` to properly import the local package:

```toml
[tool.marimo.runtime]
pythonpath = ["src"]
```

## CI/CD Integration

### Marimo Workflow

The `.github/workflows/rhiza_marimo.yml` workflow automatically:

1. Discovers all `.py` files in this directory
2. Runs each notebook in a fresh environment
3. Verifies that notebooks can bootstrap themselves
4. Ensures reproducibility

This guarantees that all notebooks remain functional and up-to-date.

### Book Workflow

The `.github/workflows/rhiza_book.yml` workflow builds the documentation book, including:

1. Exporting Marimo notebooks to static HTML
2. Generating API documentation
3. Creating test coverage reports
4. Deploying to GitHub Pages

#### Custom Environment Variables for Notebooks

The book workflow supports passing custom environment variables and secrets to notebooks during the build process. This is useful when your notebooks need access to API keys, database URLs, or other configuration values.

**Recommended Approach: Using .env.marimo file**

This approach doesn't require modifying the workflow file, so it won't be affected by template sync:

1. **Create `.env.marimo`** in your repository root:
   ```bash
   # .env.marimo
   API_KEY=your-api-key-here
   DATABASE_URL=postgresql://localhost/mydb
   DEBUG_MODE=true
   ```

2. **The workflow automatically sources this file** before building the book. No workflow changes needed!

3. **Access in your notebook**:
   ```python
   import os
   
   api_key = os.environ.get('API_KEY')
   database_url = os.environ.get('DATABASE_URL')
   ```

4. **For secrets in GitHub Actions**:
   - Store the secret value in GitHub Settings > Secrets and variables > Actions
   - Create `.env.marimo` with placeholder values for local development
   - In GitHub Actions, the secrets will be available as environment variables

**Alternative Approach: Direct workflow env: section**

If you prefer to define variables directly in the workflow (requires modifying the workflow file):

1. **Define secrets or variables** in GitHub repository settings:
   - Go to Settings > Secrets and variables > Actions
   - Create secrets (for sensitive data) or variables (for non-sensitive config)

2. **Update the workflow** (`.github/workflows/rhiza_book.yml`):
   ```yaml
   - name: "Make the book"
     env:
       API_KEY: ${{ secrets.MARIMO_ENV_API_KEY }}
       DATABASE_URL: ${{ vars.MARIMO_ENV_DATABASE_URL }}
     run: |
       # ... existing commands
   ```

3. **Access in your notebook**:
   ```python
   import os
   
   api_key = os.environ.get('API_KEY')
   database_url = os.environ.get('DATABASE_URL')
   ```

**Note**: 
- `.env.marimo` is gitignored to protect sensitive data
- The file won't be overwritten by template sync operations
- For local development, you can create `.env.marimo` with test values

## Creating New Notebooks

To create a new Marimo notebook:

1. Create a new `.py` file in this directory:
   ```bash
   marimo edit book/marimo/my_notebook.py
   ```

2. Add inline metadata at the top:
   ```python
   # /// script
   # requires-python = ">=3.11"
   # dependencies = [
   #     "marimo==0.18.4",
   #     # ... other dependencies
   # ]
   # ///
   ```

3. Start building your notebook with cells

4. Test it runs in a clean environment:
   ```bash
   uv run book/marimo/my_notebook.py
   ```

5. Commit and push - the CI will validate it automatically

## Learn More

- **Marimo Documentation**: [https://docs.marimo.io/](https://docs.marimo.io/)
- **Example Gallery**: [https://marimo.io/examples](https://marimo.io/examples)
- **Community Discord**: [https://discord.gg/JE7nhX6mD8](https://discord.gg/JE7nhX6mD8)

## Tips

- **Reactivity**: Remember that cells automatically re-run when their dependencies change
- **Pure Python**: Edit notebooks in any text editor, not just Marimo's UI
- **Git-Friendly**: Notebooks diff and merge like regular Python files
- **Self-Contained**: Use inline metadata to make notebooks reproducible
- **Interactive**: Take advantage of Marimo's rich UI components for better user experience

---

*Happy exploring with Marimo! 🚀*
