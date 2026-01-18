# SBOM Testing

This directory contains tests for SBOM (Software Bill of Materials) generation.

## What is SBOM?

A Software Bill of Materials (SBOM) is a comprehensive inventory of all components, libraries, and dependencies used in a software application. It provides:

- **Supply Chain Transparency**: Know exactly what's in your software
- **Security**: Quickly identify vulnerable dependencies
- **Compliance**: Meet regulatory requirements for software composition
- **License Management**: Track all software licenses in use

## Test Coverage

The `test_sbom.py` file includes tests for:

1. **SPDX JSON Format**: Industry-standard format by the Linux Foundation
2. **CycloneDX JSON Format**: OWASP standard for software supply chain
3. **Metadata Validation**: Ensures generated SBOMs contain proper metadata
4. **Real Repository Testing**: Validates SBOM generation on the actual rhiza codebase

## Running Tests

```bash
# Run all SBOM tests
pytest tests/test_rhiza/test_sbom.py -v

# Run a specific test
pytest tests/test_rhiza/test_sbom.py::test_sbom_generation_spdx -v
```

## Manual SBOM Generation

Generate SBOM files manually using the Makefile target:

```bash
make sbom
```

This will create:
- `sbom.spdx.json` - SPDX format
- `sbom.cyclonedx.json` - CycloneDX format

Both formats are included in the `.gitignore` to avoid committing them to the repository.

## CI/CD Integration

SBOM files are automatically generated during the release workflow:

1. The `sbom` job runs after the build phase
2. Uses [Syft](https://github.com/anchore/syft) to scan the repository and dist artifacts
3. Generates both SPDX and CycloneDX formats
4. Attaches SBOM files to the GitHub release

See `.github/workflows/rhiza_release.yml` for implementation details.

## Tools Used

- **[Syft](https://github.com/anchore/syft)**: Open-source SBOM generation tool by Anchore
- **uvx**: Used to run Syft without permanent installation

## References

- [SPDX Specification](https://spdx.dev/)
- [CycloneDX Specification](https://cyclonedx.org/)
- [NTIA Minimum Elements for SBOM](https://www.ntia.gov/files/ntia/publications/sbom_minimum_elements_report.pdf)
- [Executive Order on Cybersecurity (SBOM requirements)](https://www.whitehouse.gov/briefing-room/presidential-actions/2021/05/12/executive-order-on-improving-the-nations-cybersecurity/)
