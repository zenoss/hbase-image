#!/bin/bash
/opt/opentsdb/build/tsdb uid --config /opt/zenoss/etc/opentsdb/opentsdb.conf grep metrics | awk -e '{print $2}' | sed -e 's/:$//'

