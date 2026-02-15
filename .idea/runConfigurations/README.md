# IntelliJ IDEA / PyCharm Run Configurations

This directory contains pre-configured run configurations for IntelliJ IDEA and PyCharm that provide easy access to common Rhiza make targets.

## Features

- ✅ One-click access to all common make targets
- ✅ Organized configurations for development, testing, documentation, and deployment
- ✅ Proper environment setup for each task
- ✅ No manual configuration required

## Available Configurations

### Development

- **Install** - Install dependencies and set up environment (`make install`)
- **Clean** - Clean build artifacts and stale branches (`make clean`)
- **Tutorial** - Run interactive tutorial (`make tutorial`)

### Testing & Quality

- **Test All** - Run all tests with coverage (`make test`)
- **Run All CI Checks** - Run all CI checks locally (`make all`)
- **Check Dependencies** - Check for unused/missing dependencies (`make deptry`)
- **Type Check** - Run type checking (`make typecheck`)
- **Security Scan** - Run security scans (`make security`)
- **Format Code** - Format and lint code (`make fmt`)

### Documentation

- **Generate Docs** - Generate API documentation (`make docs`)
- **Build Book** - Build companion book (`make book`)

### Release Management

- **Bump Version (Patch)** - Bump patch version (`make bump BUMP=patch`)
- **Bump Version (Minor)** - Bump minor version (`make bump BUMP=minor`)
- **Bump Version (Major)** - Bump major version (`make bump BUMP=major`)
- **Publish (Bump + Release)** - Full release workflow (`make publish`)

## Usage

### Running a Configuration

1. **Method 1: Run Menu**
   - Click **Run** → **Run...** (or press `Alt+Shift+F10` / `Ctrl+Option+R`)
   - Select the configuration you want to run

2. **Method 2: Run Widget**
   - Click the run configuration dropdown in the toolbar
   - Select a configuration
   - Click the green play button (or press `Shift+F10` / `Ctrl+R`)

3. **Method 3: Search Everywhere**
   - Press `Shift` twice to open Search Everywhere
   - Type the configuration name
   - Press `Enter` to run

### Creating Custom Configurations

To add your own custom make targets:

1. Go to **Run** → **Edit Configurations...**
2. Click the **+** button
3. Select **Makefile** from the list
4. Configure:
   - **Name**: Display name for your configuration
   - **Target**: The make target to run (e.g., `test`, `docs`)
   - **Arguments**: Any additional arguments (e.g., `BUMP=patch`)
   - **Working Directory**: Leave as `$PROJECT_DIR$`
5. Click **OK** to save

Example custom configuration:
```
Name: Deploy to Dev
Target: deploy
Arguments: ENV=dev
```

### Keyboard Shortcuts

Once a configuration is selected, you can use:

- `Shift+F10` (Windows/Linux) or `Ctrl+R` (macOS) - Run selected configuration
- `Shift+F9` (Windows/Linux) or `Ctrl+D` (macOS) - Debug selected configuration
- `Ctrl+Shift+F10` (Windows/Linux) or `Ctrl+Shift+R` (macOS) - Run context configuration

## How They Work

These XML files define run configurations that IntelliJ IDEA / PyCharm automatically loads when you open the project. Each configuration:

1. Points to the project's `Makefile`
2. Specifies which target to run
3. Optionally includes arguments (like `BUMP=patch`)
4. Uses the project directory as working directory

The configurations use the `MAKEFILE_TARGET_RUN_CONFIGURATION` type, which requires the Makefile plugin (bundled with IntelliJ IDEA Ultimate and PyCharm Professional).

## Requirements

### IntelliJ IDEA

- **IntelliJ IDEA Ultimate** - Makefile support is built-in
- **IntelliJ IDEA Community** - Install the [Makefile Language](https://plugins.jetbrains.com/plugin/9333-makefile-language) plugin

### PyCharm

- **PyCharm Professional** - Makefile support is built-in
- **PyCharm Community** - Install the [Makefile Language](https://plugins.jetbrains.com/plugin/9333-makefile-language) plugin

To check if the plugin is installed:
1. Go to **File** → **Settings** → **Plugins**
2. Search for "Makefile"
3. Ensure "Makefile Language" plugin is enabled

## Customization

### Modifying Configurations

You can edit any configuration:

1. Go to **Run** → **Edit Configurations...**
2. Select the configuration you want to modify
3. Make your changes
4. Click **OK**

Changes made in the UI will update the corresponding XML file in this directory.

### Environment Variables

To add environment variables to a configuration:

1. Edit the configuration
2. In the **Environment variables** field, add your variables
3. Format: `KEY1=value1;KEY2=value2`

Example:
```
ENV=dev;LOG_LEVEL=debug
```

### Run Before Launch

To run tasks before a configuration executes:

1. Edit the configuration
2. Scroll to **Before launch** section
3. Click **+** to add tasks
4. Common options:
   - Run another configuration
   - Run external tool
   - Run Makefile target

Example: Run `make fmt` before `make test`:
1. Edit "Test All" configuration
2. Add "Run Makefile target" before launch
3. Select target: `fmt`

## Troubleshooting

### Configurations Don't Appear

If the run configurations don't appear in your IDE:

1. **Check Plugin**: Ensure the Makefile Language plugin is installed and enabled
2. **Reload Project**: Try **File** → **Invalidate Caches / Restart...**
3. **Check Files**: Verify XML files exist in `.idea/runConfigurations/`
4. **Manual Import**: Go to **Run** → **Edit Configurations...** → Import

### "Makefile Not Found" Error

If you get an error about the Makefile not being found:

1. Ensure you're running the configuration from the project root
2. Check that `Makefile` exists in the project root
3. Verify the working directory is set to `$PROJECT_DIR$`

### Make Target Not Found

If a make target doesn't exist:

1. Run `make help` in terminal to see available targets
2. Edit the configuration to use a valid target
3. Or add the target to your project's Makefile

### Permission Denied

On Unix systems, ensure the Makefile has execute permissions:

```bash
chmod +x Makefile
```

## File Structure

Each XML file follows this structure:

```xml
<component name="ProjectRunConfigurationManager">
  <configuration default="false" name="Display Name" type="MAKEFILE_TARGET_RUN_CONFIGURATION" factoryName="Makefile">
    <makefile filename="$PROJECT_DIR$/Makefile" target="make-target" workingDirectory="" arguments="KEY=value">
      <envs />
    </makefile>
    <method v="2" />
  </configuration>
</component>
```

- `name`: Display name in the IDE
- `target`: Make target to run
- `arguments`: Command-line arguments (optional)
- `envs`: Environment variables (optional)

## Best Practices

1. **Use Descriptive Names**: Name configurations clearly (e.g., "Test All" not just "Test")
2. **Group Related Tasks**: Use naming prefixes to group configurations
3. **Set Defaults**: Mark frequently-used configurations as default
4. **Share Configurations**: Commit `.idea/runConfigurations/` to version control
5. **Document Custom Configs**: Add comments explaining complex configurations

## Integration with Other IDEs

While these configurations are specific to IntelliJ IDEA / PyCharm, similar functionality is available in:

- **VS Code**: See `.vscode/tasks.json` for VS Code task definitions
- **Vim/Neovim**: Use makeprg or task runners like AsyncRun
- **Emacs**: Use compile commands or projectile

## See Also

- [Tools Reference](../../docs/TOOLS_REFERENCE.md) - Complete command reference
- [Quick Reference](../../docs/QUICK_REFERENCE.md) - Quick command reference
- [Extending Rhiza](../../docs/EXTENDING_RHIZA.md) - How to add custom targets
- [VS Code Tasks](../.vscode/tasks.json) - VS Code task definitions

---

*Last updated: 2026-02-15*
