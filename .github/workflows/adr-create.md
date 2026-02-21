---
on:
  workflow_dispatch:
    inputs:
      title:
        description: "ADR title (e.g., 'Use PostgreSQL for data storage')"
        required: true
        type: string
      context:
        description: "Brief context or problem statement (optional)"
        required: false
        type: string

description: "Create a new Architecture Decision Record (ADR) with AI assistance"

engine: copilot

permissions:
  contents: read

tools:
  github:
    toolsets: [repos, pull_requests]

safe-outputs:
  create-pull-request:

network:
  allowed:
    - defaults

timeout-minutes: 10
---

# Create Architecture Decision Record (ADR)

You are tasked with creating a new Architecture Decision Record (ADR) for the Rhiza project.

## Input Parameters

- **Title**: {{ inputs.title }}
- **Context** (if provided): {{ inputs.context }}

## Project Context

This is a Rhiza-based Python project that maintains ADRs in `docs/adr/`. The ADR system follows these conventions:

- **Location**: `docs/adr/` directory
- **Naming**: Files use 4-digit sequential numbering: `XXXX-title-with-hyphens.md` (e.g., `0002-use-postgresql.md`)
- **Template**: `docs/adr/0000-adr-template.md` defines the standard format
- **Index**: `docs/adr/README.md` maintains a table of all ADRs

### ADR Format

Each ADR must include:

1. **Title**: `# [NUMBER]. [TITLE]` (e.g., `# 2. Use PostgreSQL for Data Storage`)
2. **Date**: Current date in `YYYY-MM-DD` format
3. **Status**: `Proposed` (default for new ADRs)
4. **Context**: Why is this decision needed? What problem are we solving?
5. **Decision**: What approach are we taking?
6. **Consequences**: What becomes easier or harder? (Positive, Neutral, Negative)

## Instructions

### Step 1: Determine ADR Number

1. Read `docs/adr/README.md` to find the current ADR index table
2. Identify the highest numbered ADR
3. Use the next sequential 4-digit number (e.g., if latest is 0001, use 0002)

### Step 2: Create Filename Slug

Convert the title to a filename-friendly slug:
- Convert to lowercase
- Replace spaces with hyphens
- Remove special characters
- Example: "Use PostgreSQL for Data Storage" → "use-postgresql-for-data-storage"

### Step 3: Generate ADR Content

Create a comprehensive ADR with the following:

**Context Section**:
- If context was provided in inputs, use it as a starting point
- Expand with research about:
  - Why this decision is needed for Rhiza
  - What problem or requirement motivates it
  - Current state and limitations (if applicable)
- Be specific and thorough (3-5 paragraphs)

**Decision Section**:
- Clearly state what is being decided
- Explain the approach or solution
- Include key technical details
- List alternatives considered (if applicable)
- Be concrete and actionable

**Consequences Section**:
Analyze and document:
- **Positive**: Benefits, improvements, what becomes easier
- **Neutral**: Trade-offs, things that change but aren't clearly better/worse
- **Negative**: Costs, limitations, what becomes harder

Each section should have 2-4 bullet points with substantive detail.

### Step 4: Create the ADR File

1. Copy the template: `docs/adr/0000-adr-template.md` → `docs/adr/XXXX-slug.md`
2. Replace all template placeholders with actual content:
   - `[NUMBER]` → actual number
   - `[TITLE]` → actual title
   - `[YYYY-MM-DD]` → current date
   - `[Proposed | ...]` → `Proposed`
   - Fill in Context, Decision, and Consequences sections
3. Ensure all sections are complete and well-written

### Step 5: Update the Index

Edit `docs/adr/README.md`:
1. Add a new row to the ADR Index table:
   ```
   | [XXXX](XXXX-slug.md) | Title | Proposed | YYYY-MM-DD |
   ```
2. Insert it in numerical order (usually at the end)
3. Keep table formatting aligned

### Step 6: Create Pull Request

1. Create a new branch: `adr/XXXX-slug`
2. Commit both files with message: `Add ADR-XXXX: [Title]`
3. Create a pull request with:
   - **Title**: `ADR: [Title]`
   - **Description**: Brief summary of the ADR and request for review
   - **Labels**: `documentation`, `adr`

## Guidelines

- **Be thorough**: ADRs are permanent records. Make them comprehensive.
- **Research context**: If the input context is brief, research the topic to provide fuller context.
- **Consider alternatives**: Mention other approaches that were or could be considered.
- **Be honest about trade-offs**: Document both benefits and costs.
- **Use professional tone**: Clear, factual, objective writing.
- **Follow template exactly**: Don't add or remove sections from the standard format.

## Example ADR Structure

```markdown
# 2. Use PostgreSQL for Data Storage

Date: 2026-02-21

## Status

Proposed

## Context

Rhiza currently stores all configuration data in YAML files. As the system grows...
[3-5 paragraphs explaining the problem and motivation]

## Decision

We will adopt PostgreSQL as the primary data store for Rhiza configuration data...
[2-4 paragraphs detailing the decision and approach]

## Consequences

### Positive

- **Improved query capabilities**: PostgreSQL enables complex queries...
- **Better concurrency**: ACID transactions prevent data corruption...
- **Scalability**: Can handle larger datasets...

### Neutral

- **Operational complexity**: Requires PostgreSQL installation...
- **Learning curve**: Team needs to learn SQL...

### Negative

- **Migration effort**: Existing YAML data must be migrated...
- **Infrastructure dependency**: Requires database server...
```

## Success Criteria

- ADR file created with next sequential number
- All template sections filled with substantial, thoughtful content
- Index updated with new ADR entry
- Pull request created for review
- Files follow naming conventions exactly
