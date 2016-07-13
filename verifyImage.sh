#!/bin/bash

if [ $# -ne 2 ]; then
	echo "ERROR: invalid argument count. Got $# arguments; should be exactly 2"
	exit 1
fi

#
# Note that the "/v1/repositories" API on docker hub is not necessarily a publicly documented
#     API (despite the fact that it's referenced in several StackOverflow posts). The main advantages
#     are that (A) it lists all tags, and (B) does not require authentication.
#
echo "Checking for $1:$2"
curl --silent https://registry.hub.docker.com/v1/repositories/$1/tags | grep "\"name\": \"${2}\"" >/dev/null

if [ $? -eq 0 ]; then
	echo "ERROR: Docker image $1:$2 already exists"
	exit 1
fi
echo "Docker image $1:$2 does not exist"
