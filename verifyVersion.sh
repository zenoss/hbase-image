#!/bin/bash

if [ $# -ne 1 ]; then
	echo "ERROR: invalid argument count. Got $# arguments; should be exactly 1"
	exit 1
fi

echo "${1}" | grep "[-\_][a-zA-Z]*" >/dev/null

if [ $? -eq 0 ]; then
	echo "VERSION=${1} is NOT ok"
	exit 1
else
	echo "VERSION=${1} ok"
fi
