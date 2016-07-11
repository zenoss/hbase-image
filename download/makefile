include ../versions.mk

HBASE_INSTALL    := https://archive.apache.org/dist/hbase/$(HBASE_VERSION)/$(HBASE_TARBALL)
OPENTSDB_INSTALL := https://github.com/OpenTSDB/opentsdb/releases/download/v$(OPENTSDB_VERSION)/$(OPENTSDB_TARBALL)
HADOOP_INSTALL   := https://archive.apache.org/dist/hadoop/core/hadoop-$(HADOOP_VERSION)/$(HADOOP_TARBALL)
ESAPI_INSTALL    := https://github.com/apache/hbase/blob/rel/$(HBASE_VERSION)/hbase-server/src/main/resources/ESAPI.properties
ZK_URL           := http://archive.apache.org/dist/zookeeper/zookeeper-$(ZK_VERSION)/$(ZK_TARBALL)

all: hbase hadoop opentsdb

hbase: build/$(HBASE_TARBALL) build/$(ESAPI_FILE)

hadoop: build/$(HADOOP_TARBALL)

opentsdb: build/$(OPENTSDB_TARBALL)

build:
	mkdir -p build

build/$(HADOOP_TARBALL): | build
	wget -O $@ $(HADOOP_INSTALL)

build/$(HBASE_TARBALL): | build
	wget -O $@ $(HBASE_INSTALL)

build/$(OPENTSDB_TARBALL): | build
	wget -O $@ $(OPENTSDB_INSTALL)

# There is a bug in Hbase 1.1.4 that causes this file to be missing.
build/$(ESAPI_FILE): | build
	wget -O $@ $(ESAPI_INSTALL)

push:
	scp build/* zenpip.zendev.org:/home/pypiserver/packages

clean: 
	rm -rf build
