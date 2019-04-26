#!/bin/bash

name=$1

if [ "$name" = "" ]; then
    for file in *.template.yml; do
        python generate.py $file
    done
else
    python generate.py ${name}.template.yml
fi


rm ~/code/mongo-java-driver/driver-core/src/test/resources/client-side-encryption/*.json

if [ "$name" = "" ]; then
    cp *.json ~/code/mongo-java-driver/driver-core/src/test/resources/client-side-encryption
else
    cp ${name}.json ~/code/mongo-java-driver/driver-core/src/test/resources/client-side-encryption
fi
