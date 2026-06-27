# ClusterFuzzLite build image.
# Uses the OSS-Fuzz Python base image, which provides Atheris and
# the compile_python_fuzzer helper.
# Pinned by SHA256 so the build image only changes through reviewed updates.
FROM gcr.io/oss-fuzz-base/base-builder-python@sha256:3b846e1f290ce8c05608f497ec14ffce8f5f84972fd5ad026fd8bff76df17d56

COPY . $SRC/
WORKDIR $SRC
COPY .clusterfuzzlite/build.sh $SRC/build.sh
