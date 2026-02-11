# Base image with Python 3.14
FROM mcr.microsoft.com/devcontainers/python:3.14

# Update OS packages to fix kernel header vulnerabilities
# CVE-2025-38248, CVE-2025-40170, CVE-2025-68800, CVE-2025-68811, CVE-2025-71085
# CVE-2025-71116, CVE-2026-22984, CVE-2026-22990, CVE-2026-23001, CVE-2026-23010
# CVE-2026-23050, CVE-2026-23054, CVE-2026-23074, CVE-2026-23084, CVE-2026-23097
# Temporarily remove yarn repo to avoid GPG key issues, then update packages
RUN rm -f /etc/apt/sources.list.d/yarn.list \
    && apt-get update \
    && apt-get upgrade -y linux-libc-dev \
    && rm -rf /var/lib/apt/lists/*

# Update setuptools to fix Python package vulnerabilities
# CVE-2026-23949 (jaraco.context: path traversal)
# CVE-2026-24049 (wheel: privilege escalation)
RUN pip install --no-cache-dir --upgrade setuptools

# Verify updated versions
RUN dpkg -l linux-libc-dev && pip show setuptools
