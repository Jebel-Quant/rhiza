# 7. Support Dual CI/CD with GitHub Actions and GitLab CI

Date: 2024-08-01

## Status

Accepted

## Context

Rhiza aims to be the go-to template system for Python projects across organisations of
all sizes. A significant fraction of professional software teams host their code on
GitLab—either GitLab.com or self-hosted instances—rather than GitHub. These teams face
the same configuration drift problems that Rhiza solves, but a GitHub-only template
system provides no value to them.

At the same time, maintaining feature parity between two CI/CD platforms is non-trivial:

- The YAML syntax for GitHub Actions and GitLab CI differs substantially.
- Caching, secret handling, environment variable injection, and job dependency
  expressions all have platform-specific APIs.
- Keeping two implementations in sync as features are added requires discipline and
  additional testing.

The alternative—maintaining two separate Rhiza forks, one per platform—would fragment
the project and dilute maintenance effort.

## Decision

We will maintain CI/CD workflow configurations for both **GitHub Actions** and
**GitLab CI/CD** as first-class template citizens, with a goal of feature parity
between the two platforms.

**Key aspects:**

1. **GitHub Actions**: Workflows live in `.github/workflows/` with the naming convention
   `rhiza_<feature>.yml`. This is the primary platform and the one used for Rhiza's own
   CI.
2. **GitLab CI**: Workflows live in `.gitlab/workflows/` with the naming convention
   `rhiza_<feature>.yml`. A root `.gitlab-ci.yml` includes the individual workflow files.
3. **Template bundles**: The `github` bundle includes GitHub Actions workflows; the
   `gitlab` bundle includes GitLab CI workflows. Downstream projects select one or both.
4. **Parallel feature set**: Both platforms cover the same features: CI testing, release
   automation, dependency checking, pre-commit validation, documentation building, and
   template synchronization.
5. **Documentation**: `.gitlab/COMPARISON.md` documents the differences between
   platform implementations, and `.gitlab/README.md` provides GitLab-specific setup
   instructions.
6. **Testing**: The `gitlab` bundle includes its own testing documentation
   (`.gitlab/TESTING.md`) for validating GitLab-specific behaviour.

## Consequences

### Positive

- **Broader adoption**: Teams using GitLab can benefit from Rhiza's living templates
  without needing to adapt GitHub-specific workflows.
- **Platform-agnostic value proposition**: Rhiza becomes a cross-platform tool, not
  a GitHub-specific one.
- **Reduced duplication for mixed organisations**: Teams that use both GitHub and GitLab
  (e.g., mirroring, or different teams on different platforms) can maintain consistency
  from a single template source.

### Neutral

- **Platform-specific setup**: GitLab CI requires configuring CI variables (equivalent
  to GitHub secrets) and may need a GitLab token for template sync. These differences
  are documented.
- **Testing complexity**: Rhiza's own CI runs on GitHub, so GitLab workflow correctness
  must be validated via the documentation and community feedback rather than automated
  integration tests.

### Negative

- **Maintenance overhead**: Every new CI/CD feature must be implemented twice—once for
  each platform. This doubles the authoring effort for workflow changes.
- **Parity drift risk**: GitHub Actions and GitLab CI evolve independently. Features
  available on one platform may not have a clean equivalent on the other, leading to
  partial parity over time.
