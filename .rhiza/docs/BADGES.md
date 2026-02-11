# Rhiza Status Badges

This document provides ready-to-use badge templates for downstream projects that use Rhiza.

## Sync Status Badge

Display when your project was last synchronized with the Rhiza template repository.

### Dynamic Sync Badge (Recommended)

Shows the actual timestamp of your last successful sync from the GitHub Actions API:

```markdown
![Rhiza Sync](https://img.shields.io/badge/dynamic/json?label=rhiza%20sync&query=%24.workflow_runs%5B0%5D.updated_at&url=https%3A%2F%2Fapi.github.com%2Frepos%2F{owner}%2F{repo}%2Factions%2Fworkflows%2Frhiza_sync.yml%2Fruns%3Fbranch%3Dmain%26status%3Dcompleted%26per_page%3D1&color=2FA4A9)
```

**Usage:**
1. Replace `{owner}` with your GitHub username or organization name
2. Replace `{repo}` with your repository name
3. The badge will automatically update when the sync workflow runs

**Example for `jebel-quant/my-project`:**

```markdown
![Rhiza Sync](https://img.shields.io/badge/dynamic/json?label=rhiza%20sync&query=%24.workflow_runs%5B0%5D.updated_at&url=https%3A%2F%2Fapi.github.com%2Frepos%2Fjebel-quant%2Fmy-project%2Factions%2Fworkflows%2Frhiza_sync.yml%2Fruns%3Fbranch%3Dmain%26status%3Dcompleted%26per_page%3D1&color=2FA4A9)
```

### Static "Synced with Rhiza" Badge

Simple badge indicating your project uses Rhiza:

```markdown
![Synced with Rhiza](https://img.shields.io/badge/synced%20with-rhiza-2FA4A9?color=2FA4A9)
```

**Rendered as:** ![Synced with Rhiza](https://img.shields.io/badge/synced%20with-rhiza-2FA4A9?color=2FA4A9)

## Badge Color

All badges use Rhiza's signature teal color: `#2FA4A9`

You can customize the color by changing the `color` parameter in the badge URL.

## Alternative Labels

You can customize the badge label by changing the `label` parameter:

- `rhiza%20sync` - "rhiza sync"
- `latest%20sync` - "latest sync"  
- `template%20sync` - "template sync"
- `last%20synced` - "last synced"

Example with "latest sync" label:

```markdown
![Latest Sync](https://img.shields.io/badge/dynamic/json?label=latest%20sync&query=%24.workflow_runs%5B0%5D.updated_at&url=https%3A%2F%2Fapi.github.com%2Frepos%2F{owner}%2F{repo}%2Factions%2Fworkflows%2Frhiza_sync.yml%2Fruns%3Fbranch%3Dmain%26status%3Dcompleted%26per_page%3D1&color=2FA4A9)
```

## Troubleshooting

### Badge Not Displaying

If the badge shows an error or "invalid":

1. **Check workflow file name**: Ensure your sync workflow is named `rhiza_sync.yml` in `.github/workflows/`
2. **Check repository visibility**: The GitHub API endpoint must be accessible (public repo or proper authentication)
3. **Check workflow runs**: Ensure the sync workflow has run at least once successfully
4. **Verify owner/repo**: Double-check that `{owner}` and `{repo}` are correctly replaced

### Badge Shows "unknown"

If the badge displays but shows "unknown" as the value:

1. The workflow may not have completed successfully yet
2. The API query path might be incorrect for your workflow structure
3. Check that your workflow name matches exactly: `rhiza_sync.yml`

## Custom Template Repository

If you're using a custom template repository (not `Jebel-Quant/rhiza`), you can still use these badges! The badge tracks *when your project was synced*, not *what it synced from*. The important part is that your project has the `rhiza_sync.yml` workflow configured.

## More Information

For more details on setting up automated template synchronization, see the [Integration Guide](../../README.md#-integration-guide) in the main README.
