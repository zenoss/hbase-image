include ../versions.mk

HBASE_INSTALL    := https://archive.apache.org/dist/hbase/$(HBASE_VERSION)/$(HBASE_TARBALL)
OPENTSDB_INSTALL := https://github.com/OpenTSDB/opentsdb/releases/download/v$(OPENTSDB_VERSION)/$(OPENTSDB_TARBALL)
HADOOP_INSTALL   := https://archive.apache.org/dist/hadoop/core/hadoop-$(HADOOP_VERSION)/$(HADOOP_TARBALL)
ESAPI_INSTALL    := https://github.com/apache/hbase/blob/rel/$(HBASE_VERSION)/hbase-server/src/main/resources/ESAPI.properties
ZK_INSTALL       := http://archive.apache.org/dist/zookeeper/zookeeper-$(ZK_VERSION)/$(ZK_TARBALL)

all: hbase hadoop opentsdb zookeeper

hbase: build/$(HBASE_TARBALL) build/$(ESAPI_FILE)

hadoop: build/$(HADOOP_TARBALL)

opentsdb: build/$(OPENTSDB_TARBALL)

zookeeper: build/$(ZK_TARBALL)

build:
	mkdir -p build

build/$(HADOOP_TARBALL): | build
	curl --fail -o $@ $(HADOOP_INSTALL)

build/$(HBASE_TARBALL): | build
	curl --fail -o $@ $(HBASE_INSTALL)

build/$(OPENTSDB_TARBALL): | build
	curl --fail -o $@ $(OPENTSDB_INSTALL)

build/$(ZK_TARBALL): | build
	curl --fail -o $@ $(ZK_INSTALL)

# There is a bug in Hbase 1.1.4 that causes this file to be missing.
build/$(ESAPI_FILE): | build
	curl --fail -o $@ $(ESAPI_INSTALL)

push:
	scp build/* zenpip.zendev.org:/home/pypiserver/packages

clean: 
	rm -rf build
