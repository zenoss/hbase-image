#!/bin/bash
# Run HBase in the foreground

CONFIG_FILE=$1
INSTANCE_ID=${2:-0}
ENV_FILE=${3:-/etc/hbase-env.sh}

mkdir -p /var/log/hbase

[ -n "$CONFIG_FILE" ] && cp $CONFIG_FILE /opt/hbase/conf
[ -n "$ENV_FILE" ] && cp $ENV_FILE /opt/hbase/conf

export HBASE_ROOT_LOGGER=INFO,RFA
export HBASE_LOGFILE=hbase-master.log


# Now, some hackery. Because of serviced proxying connections, HBase master
# sees incoming RegionServer connections as originating from the gateway.
# We're going to allow it to resolve the gateway as localhost, so clients
# asking ZooKeeper for RegionServer addresses get localhost:60200 (which works)
# instead of 172.17.42.1:60200 (which doesn't).
source /etc/profile.d/controlcenter.sh
cat /etc/hosts > /etc/new-hosts
for ip in $CONTROLPLANE_HOST_IPS; do
    echo "$ip localhost"
done >> /etc/new-hosts
umount /etc/hosts 2>/dev/null
mv /etc/new-hosts /etc/hosts

setuser hbase /opt/hbase/bin/hbase rest -p 61000 start >/dev/null &

exec setuser hbase /opt/hbase/bin/hbase master \
    -D java.net.preferIPv4Stack=true \
    -D hbase.master.ipc.address=0.0.0.0 \
    -D hbase.master.port=$(expr 60000 + $INSTANCE_ID) \
    -D hbase.master.info.port=$(expr 60010 + $INSTANCE_ID) \
    start
