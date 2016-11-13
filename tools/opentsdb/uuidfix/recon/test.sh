#!/bin/bash

#./ddrp.py --tsdb-bin ./faketsdb.py  -m reprocess.in/log/export10-metrics.txt --logconfig-destination ./dummyconfig/logback.xml -o reprocess.out -i reprocess.in -n 2 -v -t 20161107-141548
./ddrp.py --tsdb-bin ./fakeopentsdb.sh  -m reprocess.in/log/export10-metrics.txt --logconfig-destination ./dummyconfig/logback.xml -o reprocess.out -i reprocess.in -n 2 -t 20161107-141548

