# ClusterFuzzLite build image.
# Uses the OSS-Fuzz Python base image, which provides Atheris and
# the compile_python_fuzzer helper.
# Pinned by SHA256 so the build image only changes through reviewed updates.
FROM gcr.io/oss-fuzz-base/base-builder-python@sha256:5a4612c556e795e67b19d748dbe74a4fd0535ef0e268086bf4ddd7437d70eb4e

COPY . $SRC/
WORKDIR $SRC
COPY .clusterfuzzlite/build.sh $SRC/build.sh
