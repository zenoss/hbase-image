#!/usr/bin/env bash

rm -rf ./out/
mv dummyconfig/logback.xml.bak dummyconfig/logback.xml

mv reprocess.in reprocess.in.$(date '+%Y%m%d%H%M%S')
mv reprocess.out reprocess.out.$(date '+%Y%m%d%H%M%S')
cp -r reprocess.in.bak reprocess.in


