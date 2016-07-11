#!/bin/bash

export ZK_QUORUM="$@"

echo "Starting opentsdb with ZK_QUORUM=$ZK_QUORUM"
exec supervisord -n -c /opt/zenoss/etc/supervisor/opentsdb_service.conf
