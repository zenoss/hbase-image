#!/bin/bash
# Run HBase in the foreground

CONFIG_FILE=$1
INSTANCE_ID=${2:-0}
ENV_FILE=${3:-/etc/hbase-env.sh}

mkdir -p /var/log/hbase

[ -n "$CONFIG_FILE" ] && cp $CONFIG_FILE /opt/hbase/conf
[ -n "$ENV_FILE" ] && cp $ENV_FILE /opt/hbase/conf

exec su -s /bin/bash hbase -c "/opt/hbase/bin/hbase master start 2>&1 | tee /var/log/hbase/hbase-standalone.log"
