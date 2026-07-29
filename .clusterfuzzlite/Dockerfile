# ClusterFuzzLite build image.
# Uses the OSS-Fuzz Python base image, which provides Atheris and
# the compile_python_fuzzer helper.
# Pinned by SHA256 so the build image only changes through reviewed updates.
FROM gcr.io/oss-fuzz-base/base-builder-python@sha256:485af05cc843949fd60d0e6e78b1a4922e661baf9af5eb595f9b96f563b42748

COPY . $SRC/
WORKDIR $SRC
COPY .clusterfuzzlite/build.sh $SRC/build.sh
