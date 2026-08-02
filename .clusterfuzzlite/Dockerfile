# ClusterFuzzLite build image.
# Uses the OSS-Fuzz Python base image, which provides Atheris and
# the compile_python_fuzzer helper.
# Pinned by SHA256 so the build image only changes through reviewed updates.
FROM gcr.io/oss-fuzz-base/base-builder-python@sha256:6b2b3a7e4a2da50de47f94925cffbe34747e1aae4f33d7f07ba6c681dd648b23

COPY . $SRC/
WORKDIR $SRC
COPY .clusterfuzzlite/build.sh $SRC/build.sh
