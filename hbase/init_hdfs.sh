#! /usr/bin/env bash

# Format hdfs
echo Format hdfs volume
su hdfs -c "/opt/hadoop/bin/hdfs namenode -format /" &>/dev/null

# Start up the namenode so we can set attrs on the root directory
echo Start namenode
su hdfs -c "/opt/hadoop/bin/hdfs namenode" &> /dev/null &
NAMENODE_PID=$!
while test $(curl -s -o /dev/null -w '%{http_code}' localhost:50070) != 200 ; do
    echo Wait for namenode
    sleep 3
done

# Set attributes on root directory.  It needs to be world writable so that
#  other processes (e.g., hbase) can create directories for their storage needs.
echo Set hdfs root properties
su hdfs -c "/opt/hadoop/bin/hdfs dfs -chmod 777 /"
su hdfs -c "/opt/hadoop/bin/hdfs dfs -chown hdfs:hdfs /"

# Kill the namenode process
echo Exiting
kill $NAMENODE_PID
wait $NAMENODE_PID
exit 0
