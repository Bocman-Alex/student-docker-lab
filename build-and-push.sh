#!/bin/bash
set -e

REGISTRY="docker.io"
NAMESPACE="botsman01"          
IMAGE_NAME="student-app-api"
VERSION=${VERSION:-$(git describe --tags --always --dirty 2>/dev/null || echo "v0.0.0")}

echo "Building $REGISTRY/$NAMESPACE/$IMAGE_NAME:$VERSION"
docker build -t $REGISTRY/$NAMESPACE/$IMAGE_NAME:$VERSION ./api
docker push $REGISTRY/$NAMESPACE/$IMAGE_NAME:$VERSION
echo "Published $VERSION"
