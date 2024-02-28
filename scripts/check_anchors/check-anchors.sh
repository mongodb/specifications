#!/bin/bash -ex

SCRIPT_DIR=$(dirname ${BASH_SOURCE[0]})
SCRIPT_DIR="$( cd -- "$SCRIPT_DIR" &> /dev/null && pwd )"
pushd $SCRIPT_DIR
npm install 
node index.js "$@"