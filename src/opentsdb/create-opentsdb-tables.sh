#!/bin/bash

export COMPRESSION=SNAPPY
export HBASE_HOME=/opt/hbase
export JAVA_HOME=/usr/lib/jvm/jre

# try all hosts in the zookeeper quorum
for zk_host_port in `echo $ZK_QUORUM | tr ',' ' '` ; do
  host=`echo $zk_host_port | cut -d ':' -f 1`
  port=`echo $zk_host_port | cut -d ':' -f 2`

  if [ "$port" == "$host" ] ; then
    port=2181
  fi

  #write an hbase config file
  ZK_HOST=$host ZK_PORT=$port /opt/opentsdb/configure-hbase.sh

  #create hbase tables w/multi-tenancy support
  ID=$CONTROLPLANE_TENANT_ID
  wget -qO - localhost:61000/$ID-tsdb/schema && exit 0
  /opt/opentsdb/create_table_splits.rb $ID-tsdb t 256
  TSDB_TABLE=$ID-tsdb UID_TABLE=$ID-tsdb-uid TREE_TABLE=$ID-tsdb-tree META_TABLE=$ID-tsdb-meta /opt/opentsdb/create_table_splits.sh

  #keep trying until a successful connection occurs
  if [[ `/opt/opentsdb/src/create_table.sh` == *"ERROR: Table already exists: tsdb"* ]]; then
    exit 0
  fi

  #set TTL to 90 days (7776000)
  /opt/opentsdb/set-opentsdb-table-ttl.sh 7776000

  echo `date` ": Waiting for HBase to be ready..."
  sleep 2
done
