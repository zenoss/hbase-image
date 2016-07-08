#!/bin/bash

cat > $HBASE_HOME/conf/hbase-site.xml <<EOF
<configuration>
  <property>
    <name>hbase.zookeeper.quorum</name>
    <value>$ZK_HOST</value>
  </property>
  <property>
    <name>hbase.zookeeper.property.clientPort</name>
    <value>$ZK_PORT</value>
  </property>
</configuration>
EOF
