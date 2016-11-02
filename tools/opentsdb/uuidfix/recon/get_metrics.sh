#!/bin/bash
##############################################################################
#
# Copyright (C) Zenoss, Inc. 2016, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
#
##############################################################################
/opt/opentsdb/build/tsdb uid --config /opt/zenoss/etc/opentsdb/opentsdb.conf grep . | grep -a metrics | awk -e '{print $2}' | sed -e 's/:$//'
