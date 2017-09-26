#!/bin/bash

export ZK_QUORUM="$@"
export JVMARGS="${TSDB_JAVA_MEM_MB} -XX:+ExitOnOutOfMemoryError -enableassertions -enablesystemassertions"

echo "Starting opentsdb with ZK_QUORUM=$ZK_QUORUM"
exec supervisord -n -c /opt/zenoss/etc/supervisor/opentsdb_service.conf
