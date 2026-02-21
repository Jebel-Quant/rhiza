# Architecture Decision Records

This directory contains Architecture Decision Records (ADRs) for the Rhiza project.

## What is an ADR?

An Architecture Decision Record (ADR) is a document that captures an important architectural decision made along with its context and consequences.

## ADR Format

Each ADR follows a consistent format defined in [0000-adr-template.md](0000-adr-template.md):

- **Title and Number**: Sequential numbering with descriptive title
- **Date**: When the decision was made
- **Status**: Current state (Proposed, Accepted, Deprecated, Superseded)
- **Context**: The issue or situation that motivates the decision
- **Decision**: The change or approach being taken
- **Consequences**: What becomes easier or harder as a result

## ADR Index

| Number | Title | Status | Date |
|--------|-------|--------|------|
| [0001](0001-use-architecture-decision-records.md) | Use Architecture Decision Records | Accepted | 2026-01-01 |

## Creating a New ADR

### Option 1: Using AI Assistance (Recommended)

The easiest way to create a new ADR is using the automated workflow:

```bash
make adr
```

This will:
1. Prompt you for the ADR title and optional context
2. Trigger an AI-powered workflow that generates a comprehensive ADR
3. Automatically determine the next ADR number
4. Create the ADR file with well-researched content
5. Update the index table
6. Open a pull request for review

### Option 2: Manual Creation

If you prefer to create an ADR manually:

1. Copy the template: `cp docs/adr/0000-adr-template.md docs/adr/0002-example-decision.md`
2. Use the next available 4-digit number (e.g., 0002, 0003, 0004)
3. Fill in all sections with relevant information
4. Update this README to add your ADR to the index
5. Submit via pull request for review

## Resources

- [ADR GitHub Organization](https://adr.github.io/)
- [Michael Nygard's article on ADRs](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions)
