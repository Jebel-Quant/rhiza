# Rhiza Roadmap

This document outlines the planned features, improvements, and long-term vision for the Rhiza project.

## Current Version: 0.7.5

## Vision

Rhiza aims to be the definitive solution for maintaining consistency and best practices across Python projects through living templates that evolve with your codebase. Our goal is to make it effortless for teams to adopt modern development practices and keep their projects aligned with industry standards.

## Release Timeline

### v0.8.0 - Quality & Maintainability Focus (Q1 2026)
**Theme: Developer Experience & Code Quality**

#### Completed ✅
- Project structure standardization
- Core template synchronization
- CI/CD workflow automation
- Development container support

#### In Progress 🚧
- TODO/FIXME/HACK comment tracking (`make todos`)
- Technical debt documentation system
- Enhanced changelog automation with PR categorization
- GitHub project board integration

#### Planned Features
- Automated code quality metrics dashboard
- Template customization validator
- Pre-commit hook improvements
- Documentation coverage reporting

### v0.9.0 - Enhanced Template Management (Q2 2026)
**Theme: Flexibility & Extensibility**

#### Template Features
- Multi-repository template support
- Conditional template inclusion based on project type
- Template versioning and rollback capabilities
- Custom template validation rules

#### Developer Tools
- Interactive template configuration wizard
- Conflict resolution assistant for sync operations
- Template diff visualization
- Dry-run mode improvements

#### Documentation
- Template authoring guide
- Best practices documentation
- Video tutorials for common workflows → see [rhiza-education](https://github.com/Jebel-Quant/rhiza-education)
- Migration guides from other template systems → see [rhiza-education](https://github.com/Jebel-Quant/rhiza-education)

### v1.0.0 - Production Ready (Q3 2026)
**Theme: Stability & Enterprise Features**

#### Core Improvements
- Performance optimization for large repositories
- Advanced caching mechanisms
- Parallel sync operations
- Improved error handling and recovery

#### Enterprise Features
- Private template repository support
- Organization-wide policy enforcement
- Audit logging and compliance reporting
- Role-based access controls for template management

#### Integration
- GitHub App for seamless integration
- GitLab support
- Bitbucket support
- CI/CD plugin ecosystem

#### Quality Assurance
- Comprehensive test coverage (>95%)
- Performance benchmarking suite
- Security audit and hardening
- Stability testing across diverse projects

## Future Vision (v1.1+)

### Advanced Features
- AI-assisted template recommendations
- Automatic detection of configuration drift
- Smart merge conflict resolution
- Template marketplace/registry

### Ecosystem Growth
- Plugin system for custom template processors
- Language-agnostic template support (TypeScript, Rust, Go, etc.)
- Integration with popular development tools
- Community-contributed template library

### Platform Enhancements
- Web-based template management dashboard
- Real-time collaboration on template changes
- Analytics and insights on template usage
- Automated security vulnerability scanning in templates

## Contributing to the Roadmap

We welcome community input on our roadmap! Here's how you can contribute:

1. **Feature Requests**: Open an issue with the `enhancement` label
2. **Discussions**: Join conversations in GitHub Discussions
3. **Voting**: React with 👍 on issues you'd like to see prioritized
4. **Implementation**: Submit PRs for features you'd like to contribute

## Prioritization Criteria

We prioritize features based on:
- **Impact**: How many users will benefit
- **Effort**: Development and maintenance cost
- **Alignment**: Fit with core vision and values
- **Community**: User requests and contributions
- **Dependencies**: Prerequisites and blockers

## Release Cadence

- **Major releases** (x.0.0): Quarterly, with breaking changes
- **Minor releases** (0.x.0): Monthly, with new features
- **Patch releases** (0.0.x): As needed, for bug fixes

## Stay Updated

- Watch this repository for release notifications
- Follow our [CHANGELOG](https://github.com/Jebel-Quant/rhiza/releases) for detailed updates
- Join discussions in GitHub Issues and Discussions
- Check our [documentation](docs/) for the latest guides

## Feedback

Your feedback shapes our roadmap! Please:
- Open issues for bugs and feature requests
- Share your use cases and pain points
- Contribute to discussions on proposed features
- Submit pull requests for improvements

---

**Last Updated**: February 2026  
**Next Review**: May 2026

For technical debt and known limitations, see [docs/TECHNICAL_DEBT.md](docs/TECHNICAL_DEBT.md).
