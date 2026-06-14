#!/bin/bash -eu
# ClusterFuzzLite build script — compiles each Python harness in tests/fuzz/
# via OSS-Fuzz's compile_python_fuzzer helper.

cd "$SRC/rhiza"

# Copy suppression_audit into tests/fuzz/ so PyInstaller can discover and bundle
# it into the frozen binary. Without this, the harness would dynamically load
# the file from the source tree at runtime, which is absent in the ClusterFuzzLite
# runner environment where bad_build_check executes the binary.
cp .rhiza/utils/suppression_audit.py tests/fuzz/suppression_audit.py

for fuzzer in tests/fuzz/fuzz_*.py; do
  compile_python_fuzzer "$fuzzer"
done
