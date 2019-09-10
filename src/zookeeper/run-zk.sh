#!/bin/bash

# Create the log directory
mkdir -p /var/log/zookeeper /var/run/zookeeper && \
    chown zookeeper /var/log/zookeeper /var/run/zookeeper && \
    touch /var/log/zookeeper/zookeeper.log && \
    chown zookeeper /var/log/zookeeper/zookeeper.log

# Run ZooKeeper in the foreground
exec setuser zookeeper /bin/bash -c "JVMFLAGS='-Djava.net.preferIPv4Stack=true' /usr/bin/zookeeper-server start-foreground $@ 2>&1 | tee /var/log/zookeeper/zookeeper.log"
