#!/bin/bash -eu
# ClusterFuzzLite build script — compiles each Python harness in fuzz/
# via OSS-Fuzz's compile_python_fuzzer helper.

cd "$SRC/rhiza"

for fuzzer in fuzz/fuzz_*.py; do
  compile_python_fuzzer "$fuzzer"
done
