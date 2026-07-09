#!/bin/bash -eu
# ClusterFuzzLite build script — compiles each Python harness in tests/fuzz/
# via OSS-Fuzz's compile_python_fuzzer helper.

cd "$SRC"

# Compile every Atheris harness under tests/fuzz/. `nullglob` makes the loop a
# no-op when the repo ships no harnesses (the fuzzing capability stays wired up
# but has nothing to run) instead of passing a literal glob to the compiler.
shopt -s nullglob
for fuzzer in tests/fuzz/fuzz_*.py; do
  compile_python_fuzzer "$fuzzer"
done
