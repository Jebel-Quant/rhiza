# GitHub Project Board Setup Guide

This guide walks you through setting up a GitHub Project Board for tracking enhancements, roadmap items, and technical debt for your Rhiza-based project.

## Overview

GitHub Projects (v2) provides a flexible, integrated way to track work across repositories. This guide focuses on setting up a project board specifically for maintainability tracking.

## Quick Start

### 1. Create a New Project

1. Navigate to your organization or repository on GitHub
2. Click on the **Projects** tab
3. Click **New project**
4. Choose a template:
   - **Roadmap**: For tracking planned features over time
   - **Feature**: For managing feature development
   - **Bug tracker**: For issue management
   - Or start with **Blank** for full customization

### 2. Basic Configuration

For a maintainability-focused board, we recommend:

**Project Name**: `Rhiza Maintainability Tracker`

**Description**: 
```
Tracks enhancements, roadmap items, technical debt, and quality improvements 
for the Rhiza project.
```

**Visibility**:
- **Public**: For open-source projects (recommended for transparency)
- **Private**: For internal/enterprise use

### 3. Configure Views

Create multiple views for different perspectives:

#### View 1: Roadmap View (Table)
**Purpose**: Track items chronologically

**Fields to add**:
- Status (Todo, In Progress, Done)
- Priority (Critical, High, Medium, Low)
- Effort (Small, Medium, Large)
- Quarter (Q1 2026, Q2 2026, etc.)
- Type (Feature, Enhancement, Technical Debt, Documentation)
- Assignees

**Filters**: None (show all)
**Sort**: By Quarter, then Priority

#### View 2: By Priority (Board)
**Purpose**: Kanban-style workflow

**Columns**:
- Backlog
- Todo
- In Progress
- In Review
- Done

**Group by**: Priority
**Sort**: Newest first

#### View 3: Technical Debt (Table)
**Purpose**: Focus on debt items

**Fields**: Same as Roadmap View
**Filters**: Type = "Technical Debt"
**Sort**: By Priority, then Effort

### 4. Configure Custom Fields

Add these custom fields for better tracking:

1. **Effort Estimate**
   - Type: Single select
   - Options: Small (< 1 day), Medium (1-3 days), Large (> 3 days)

2. **Priority**
   - Type: Single select
   - Options: Critical, High, Medium, Low

3. **Type**
   - Type: Single select
   - Options: Feature, Enhancement, Bug, Technical Debt, Documentation

4. **Quarter**
   - Type: Single select
   - Options: Q1 2026, Q2 2026, Q3 2026, Q4 2026, Future

5. **Impact Area**
   - Type: Single select
   - Options: Templates, CI/CD, Documentation, Developer Experience, Performance

## Linking Issues and PRs

### Automatic Linking

GitHub Projects automatically shows linked issues and PRs. To link:

1. Open an issue or PR
2. In the right sidebar, under **Projects**, click the gear icon
3. Select your project board
4. The item appears in your project

### Bulk Adding

To add multiple issues at once:

1. Open your project
2. Click **Add items** (bottom of any view)
3. Select repository
4. Choose issues to add
5. Click **Add selected items**

## Workflow Automation

Set up automations to reduce manual work:

### Auto-add Items

**Trigger**: When an issue/PR is labeled with specific labels
**Action**: Add to project with default status

Example labels:
- `enhancement` → Add to project, set Type = Enhancement
- `technical-debt` → Add to project, set Type = Technical Debt
- `documentation` → Add to project, set Type = Documentation

### Auto-move Status

1. **When PR is opened**: Move to "In Progress"
2. **When PR is reviewed**: Move to "In Review"
3. **When PR is merged**: Move to "Done"
4. **When issue is closed**: Move to "Done"

### Configure Automations

1. In your project, click **...** (top right)
2. Select **Workflows**
3. Enable built-in workflows or create custom ones
4. Configure triggers and actions

## Maintaining the Board

### Weekly Review

Every week:
1. Review "In Progress" items for blockers
2. Move completed items to "Done"
3. Prioritize "Todo" items
4. Add new items from issue backlog

### Monthly Review

Every month:
1. Review and update quarterly assignments
2. Reassess priorities based on feedback
3. Archive completed items from previous months
4. Update roadmap alignment

### Quarterly Review

Every quarter:
1. Review completed features against roadmap
2. Adjust future quarters based on progress
3. Gather stakeholder feedback
4. Update effort estimates based on actuals

## Best Practices

### Issue Creation

When creating issues for the board:

```markdown
## Description
Clear description of the enhancement or debt item

## Motivation
Why is this important? What problem does it solve?

## Proposed Solution
High-level approach (can be refined later)

## Acceptance Criteria
- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3

## Additional Context
Links to related issues, discussions, or documents
```

### Labels to Use

Recommended labels:
- `enhancement`: New features or improvements
- `technical-debt`: Code quality improvements
- `documentation`: Documentation updates
- `good-first-issue`: Easy entry points for contributors
- `help-wanted`: Issues where community help is needed
- `priority:high`, `priority:medium`, `priority:low`: Priority levels

### Integrating with ROADMAP.md

Keep your project board in sync with ROADMAP.md:

1. Major milestones from ROADMAP.md should have corresponding project views
2. Link to project board from ROADMAP.md
3. Update ROADMAP.md quarterly based on board progress
4. Reference specific issues from ROADMAP.md sections

## Advanced Features

### Insights and Reporting

GitHub Projects provides built-in insights:

1. Click **Insights** tab in your project
2. Create charts:
   - **Burn down**: Track progress toward milestones
   - **Velocity**: Measure completion rate
   - **By field**: Distribution by priority, type, etc.

### Project Templates

Save your project configuration as a template:

1. Configure a project with views, fields, and workflows
2. In project settings, enable "Template project"
3. Reuse configuration for new projects

### Integration with CI/CD

Link project status with automated checks:

```yaml
# .github/workflows/update-project.yml
name: Update Project Board
on:
  pull_request:
    types: [opened, reopened, synchronize]

jobs:
  update:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/add-to-project@v0.5.0
        with:
          project-url: https://github.com/orgs/<org>/projects/<number>
          github-token: ${{ secrets.GITHUB_TOKEN }}
```

## Resources

- [GitHub Projects Documentation](https://docs.github.com/en/issues/planning-and-tracking-with-projects)
- [Best Practices for Projects](https://docs.github.com/en/issues/planning-and-tracking-with-projects/learning-about-projects/best-practices-for-projects)
- [Automating Projects](https://docs.github.com/en/issues/planning-and-tracking-with-projects/automating-your-project)

## Example Project

For inspiration, see the Rhiza project board:
- [Rhiza Maintainability Tracker](https://github.com/orgs/Jebel-Quant/projects) (if public)

## Troubleshooting

### Items not appearing in project
- Check repository visibility matches project visibility
- Verify item is linked to project (check right sidebar in issue/PR)
- Refresh the project view

### Automations not working
- Check workflow permissions in project settings
- Verify labels match automation triggers exactly
- Review GitHub Actions logs for errors

### Performance issues
- Consider archiving old "Done" items
- Limit views to active items only
- Use filters to reduce displayed items

---

**Last Updated**: February 2026

For related documentation:
- [ROADMAP.md](../ROADMAP.md) - Project roadmap and planned features
- [TECHNICAL_DEBT.md](TECHNICAL_DEBT.md) - Known limitations and debt items
- [CONTRIBUTING.md](../CONTRIBUTING.md) - Contribution guidelines
