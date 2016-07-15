# Shared definitions for makefiles in download and root subdirectories.
HBASE_VERSION       := 1.1.4
OPENTSDB_VERSION    := 2.2.0
HADOOP_VERSION      := 2.5.2
ZK_VERSION          := 3.4.5
HDFSMETRICS_VERSION := 1.0

IMAGE_VERSION    := 24.0.0-dev

HBASE_TARBALL    := hbase-$(HBASE_VERSION)-bin.tar.gz
OPENTSDB_TARBALL := opentsdb-$(OPENTSDB_VERSION).tar.gz
HADOOP_TARBALL   := hadoop-$(HADOOP_VERSION).tar.gz
ZK_TARBALL       := zookeeper-$(ZK_VERSION).tar.gz
HDFSMETRICS_JAR  := hdfsMetrics-$(HDFSMETRICS_VERSION).jar

# Note: the ESAPI.properties file is mistakenly not included in Hadoop 1.1.4.
# Once we move to the next version of hadoop we should not have to explicitly
# include this file in the image.
ESAPI_FILE       := ESAPI-$(HBASE_VERSION).properties

