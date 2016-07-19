#!/bin/bash
# Run HBase in the foreground

CONFIG_FILE=$1
INSTANCE_ID=${2:-0}
ENV_FILE=${3:-/etc/hbase-env.sh}

mkdir -p /var/log/hbase

[ -n "$CONFIG_FILE" ] && cp $CONFIG_FILE /opt/hbase/conf
[ -n "$ENV_FILE" ] && cp $ENV_FILE /opt/hbase/conf

export HBASE_ROOT_LOGGER=INFO,RFA
export HBASE_LOGFILE=hbase-regionserver.log

echo "Sleeping 10 to allow ports to be imported by the HMaster"
sleep 10

exec setuser hbase /opt/hbase/bin/hbase regionserver \
    -D java.net.preferIPv4Stack=true \
    -D hbase.regionserver.ipc.address=0.0.0.0 \
    -D hbase.regionserver.port=$(expr 60200 + $INSTANCE_ID) \
    -D hbase.regionserver.info.port=$(expr 60300 + $INSTANCE_ID) \
    start
