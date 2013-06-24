#!/bin/sh

# This tells the build process to not ez_install pyev
NO_PYEV=true

PROJECT_NAME="meniscus"
PROJECT_VERSION="$(cat VERSION)"

python build.py meniscus
fpm -v "${PROJECT_VERSION}" -n "${PROJECT_NAME}" -t deb --after-install ./pkg/post_install.deb.sh --after-remove ./pkg/post_remove.deb.sh -s tar "./${PROJECT_NAME}_${PROJECT_VERSION}.tar.gz"
