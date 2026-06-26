# ClusterFuzzLite build image.
# Uses the OSS-Fuzz Python base image, which provides Atheris and
# the compile_python_fuzzer helper.
# Pinned by SHA256 so the build image only changes through reviewed updates.
FROM gcr.io/oss-fuzz-base/base-builder-python@sha256:e0e18dea5d2e4107a4f5d04652e6c278fbea32dc6d6861ee8de29402d0916746

COPY . $SRC/
WORKDIR $SRC
COPY .clusterfuzzlite/build.sh $SRC/build.sh
