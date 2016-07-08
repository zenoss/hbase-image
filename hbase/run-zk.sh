#!/bin/bash

# Create the log directory
mkdir -p /var/log/zookeeper /var/run/zookeeper && chown zookeeper /var/log/zookeeper /var/run/zookeeper

# Run ZooKeeper in the foreground
exec su -s /bin/bash zookeeper -c "JVMFLAGS='-Djava.net.preferIPv4Stack=true' /usr/bin/zookeeper-server start-foreground $@ 2>&1 | tee /var/log/zookeeper/zookeeper.log"
