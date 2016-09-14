# Shared definitions for makefiles in download and root subdirectories.

# Versions of third party components used in building the output images.
# When either of HBase or Hadoop is upgraded, check the pom file of hdfsMetrics
# to see if we are using the right versions of other libraries, such as Jackson,
# using a command like mvn dependency:tree -Dverbose.
HBASE_VERSION       := 1.1.4
OPENTSDB_VERSION    := 2.2.0
HADOOP_VERSION      := 2.5.2
ZK_VERSION          := 3.4.5
HDFSMETRICS_VERSION := 1.0

# Image used as the base from which the output images are built
BASE_IMAGE       := zenoss/centos-base:1.1.1-java

# Version of the output images
IMAGE_VERSION    := 24.0.3-dev

# Names of third-party component artifacts
HBASE_TARBALL    := hbase-$(HBASE_VERSION)-bin.tar.gz
OPENTSDB_TARBALL := opentsdb-$(OPENTSDB_VERSION).tar.gz
HADOOP_TARBALL   := hadoop-$(HADOOP_VERSION).tar.gz
ZK_TARBALL       := zookeeper-$(ZK_VERSION).tar.gz
HDFSMETRICS_JAR  := hdfsMetrics-$(HDFSMETRICS_VERSION).jar

# Note: the ESAPI.properties file is mistakenly not included in Hadoop 1.1.4.
# Once we move to the next version of hadoop we should not have to explicitly
# include this file in the image.
ESAPI_FILE       := ESAPI-$(HBASE_VERSION).properties

