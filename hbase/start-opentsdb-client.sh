#!/bin/bash

##
# Start an opentsdb client. The environment variables ZK_QUORUM and
# CONTROLPLANE_TENANT_ID must be set before running this script.
#

export JAVA_HOME=/usr/lib/jvm/jre

# Supervisord restarts processes by sending a SIGTERM (by default).
# Handle signals, and kill subprocesses so we don't have orphaned processes
# proliferating on each restart
trap "kill 0" SIGINT SIGTERM EXIT

if [[ $CREATE_TABLES == 1 ]]; then 
    # this script blocks until the tables are created
    /opt/opentsdb/create-opentsdb-tables.sh
fi

# configure opentsdb - http://opentsdb.net/docs/build/html/user_guide/configuration.html
ID=$CONTROLPLANE_TENANT_ID

mkdir -p /tmp/tsd

# start opentsdb
exec /opt/opentsdb/build/tsdb tsd --config /opt/zenoss/etc/opentsdb/opentsdb.conf
