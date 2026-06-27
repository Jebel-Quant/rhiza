#!/bin/bash -eu
# ClusterFuzzLite build script — compiles each Python harness in tests/fuzz/
# via OSS-Fuzz's compile_python_fuzzer helper.

cd "$SRC"

# Copy the suppression-audit modules into tests/fuzz/ so PyInstaller can discover
# and bundle them into the frozen binary. Without this, the harness would
# dynamically load the files from the source tree at runtime, which is absent in
# the ClusterFuzzLite runner environment where bad_build_check executes the binary.
# suppression_audit imports its sibling suppression_parse/suppression_report
# modules, so all three must be present for PyInstaller's static import analysis.
cp .rhiza/utils/suppression_audit.py tests/fuzz/suppression_audit.py
cp .rhiza/utils/suppression_parse.py tests/fuzz/suppression_parse.py
cp .rhiza/utils/suppression_report.py tests/fuzz/suppression_report.py

for fuzzer in tests/fuzz/fuzz_*.py; do
  compile_python_fuzzer "$fuzzer"
done
