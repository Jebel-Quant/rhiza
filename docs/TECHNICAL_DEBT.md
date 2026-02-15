# Technical Debt

This document tracks known limitations, technical debt items, and future improvements for the Rhiza project.

## Overview

Technical debt is a natural part of software development. This document helps us:
- Maintain transparency about known limitations
- Prioritize improvements systematically
- Track the evolution of our codebase
- Guide contributor efforts

## Categories

Debt items are categorized by:
- **Priority**: Critical, High, Medium, Low
- **Effort**: Small (< 1 day), Medium (1-3 days), Large (> 3 days)
- **Type**: Architecture, Code Quality, Documentation, Testing, Performance

---

## Critical Priority

### 1. Template Conflict Resolution
**Category**: Architecture | **Effort**: Large  
**Issue**: Manual conflict resolution required when template updates conflict with local changes.

**Impact**: 
- Reduces automation effectiveness
- Creates friction in sync workflow
- Requires manual intervention

**Proposed Solution**:
- Implement three-way merge strategy
- Add interactive conflict resolution UI
- Provide rollback capabilities

**Related Issues**: TBD

---

## High Priority

### 2. Test Coverage for Template Sync
**Category**: Testing | **Effort**: Medium  
**Issue**: Limited test coverage for template synchronization edge cases.

**Impact**:
- Risk of regression bugs
- Harder to refactor with confidence
- Edge cases may be undiscovered

**Proposed Solution**:
- Add integration tests for sync scenarios
- Mock Git operations for testing
- Test conflict resolution paths

**Related Issues**: TBD

### 3. Performance with Large Repositories
**Category**: Performance | **Effort**: Large  
**Issue**: Sync operations can be slow with large repositories or many files.

**Impact**:
- Poor developer experience
- Longer CI/CD times
- Resource consumption

**Proposed Solution**:
- Implement incremental sync
- Add caching layer
- Parallelize file operations
- Profile and optimize hot paths

**Related Issues**: TBD

### 4. Documentation Coverage
**Category**: Documentation | **Effort**: Medium  
**Issue**: Some advanced features lack comprehensive documentation.

**Impact**:
- Harder for new users to adopt
- Support burden on maintainers
- Feature underutilization

**Proposed Solution**:
- Audit documentation coverage
- Add examples for complex scenarios
- Create video tutorials
- Improve in-code documentation

**Related Issues**: TBD

---

## Medium Priority

### 5. Error Messages Clarity
**Category**: Code Quality | **Effort**: Small  
**Issue**: Some error messages lack actionable guidance.

**Impact**:
- Poor debugging experience
- Support requests increase
- User frustration

**Proposed Solution**:
- Review and improve error messages
- Add suggestions for common errors
- Include documentation links
- Standardize error format

**Related Issues**: TBD

### 6. Makefile Target Documentation
**Category**: Documentation | **Effort**: Small  
**Issue**: Not all Makefile targets have help text.

**Impact**:
- Reduced discoverability
- Confusion about available commands
- Incomplete `make help` output

**Proposed Solution**:
- Add `##` comments to all targets
- Document parameters and examples
- Ensure help text consistency

**Related Issues**: TBD

### 7. Dependency Version Constraints
**Category**: Code Quality | **Effort**: Medium  
**Issue**: Some dependencies lack upper bounds, risking breaking changes.

**Impact**:
- Potential for surprise breakage
- Harder to reproduce builds
- Upgrade uncertainty

**Proposed Solution**:
- Review and add upper bounds
- Document version rationale
- Setup automated testing across versions
- Use Renovate for updates

**Related Issues**: See docs/DEPENDENCIES.md

### 8. Template Validation
**Category**: Architecture | **Effort**: Medium  
**Issue**: Limited validation of custom templates before sync.

**Impact**:
- Risk of invalid configurations
- Harder to debug template issues
- Potential security risks

**Proposed Solution**:
- Add schema validation for templates
- Implement pre-sync checks
- Provide template linting
- Create template testing framework

**Related Issues**: TBD

---

## Low Priority

### 9. Internationalization
**Category**: Code Quality | **Effort**: Large  
**Issue**: No support for non-English documentation or messages.

**Impact**:
- Limited accessibility for non-English speakers
- Reduces global adoption potential

**Proposed Solution**:
- Evaluate demand for i18n
- Setup localization framework
- Translate documentation
- Accept community translations

**Related Issues**: TBD

### 10. Plugin System
**Category**: Architecture | **Effort**: Large  
**Issue**: No plugin system for extending functionality.

**Impact**:
- Limited extensibility
- Hard to add custom processors
- Monolithic codebase

**Proposed Solution**:
- Design plugin architecture
- Define plugin API
- Create plugin examples
- Setup plugin registry

**Related Issues**: See ROADMAP.md v1.1+

### 11. Legacy Python Version Support
**Category**: Code Quality | **Effort**: Medium  
**Issue**: Maintaining compatibility with Python 3.11 increases complexity.

**Impact**:
- Cannot use newest Python features
- Extra testing burden
- Backport requirements

**Proposed Solution**:
- Evaluate user base Python versions
- Consider minimum version bump
- Document migration path
- Provide transition period

**Related Issues**: TBD

---

## Recently Resolved

### ✅ UV Package Manager Migration
**Resolved in**: v0.7.0  
**Issue**: Dependency on pip and multiple tools  
**Solution**: Migrated to UV for unified dependency management

### ✅ Pre-commit Hook Standardization
**Resolved in**: v0.6.5  
**Issue**: Inconsistent pre-commit configurations  
**Solution**: Standardized hooks across templates

### ✅ GitHub Actions Modernization
**Resolved in**: v0.6.0  
**Issue**: Outdated GitHub Actions versions  
**Solution**: Updated all actions to latest stable versions

---

## Process

### Adding Technical Debt
1. Identify the issue clearly
2. Assess impact and effort
3. Add to appropriate priority section
4. Link related issues/PRs
5. Update this document

### Addressing Technical Debt
1. Select item from backlog
2. Create GitHub issue if needed
3. Implement solution
4. Move to "Recently Resolved"
5. Update related documentation

### Review Cadence
- **Monthly**: Review and re-prioritize items
- **Quarterly**: Assess resolved items and overall debt
- **Annually**: Archive old resolved items to CHANGELOG

---

## Contributing

Found technical debt? Help us improve:

1. Open an issue describing the debt item
2. Label it as `technical-debt`
3. Provide context and impact assessment
4. Suggest potential solutions
5. Link to relevant code sections

See [CONTRIBUTING.md](../CONTRIBUTING.md) for general contribution guidelines.

---

**Last Updated**: February 2026  
**Next Review**: March 2026

For planned features and improvements, see [ROADMAP.md](../ROADMAP.md).
