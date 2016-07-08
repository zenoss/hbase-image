#!/bin/bash

#!/bin/sh
# this script sets the TTL value on the tsdb column family in HBase.

TTL=$1
if ! [[ $TTL =~ ^[1-9][0-9]*$ ]] ; then
  echo "Invalid TTL value (expecting a postive integer)" 1>&2
  exit 1
fi

TABLE=${CONTROLPLANE_TENANT_ID}-tsdb
if [ "$TABLE" == "-tsdb" ] ; then
  echo "Missing Tenant ID" 1>&2
  exit 2
fi

export JAVA_HOME=/usr/lib/jvm/jre

hbh=/opt/hbase
exec "$hbh/bin/hbase" shell <<EOF
  disable '$TABLE';
  alter '$TABLE', {NAME=>'t', TTL=>'$TTL'};
  enable '$TABLE';
  describe '$TABLE'
EOF
