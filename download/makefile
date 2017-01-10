include ../versions.mk

HBASE_INSTALL    := https://archive.apache.org/dist/hbase/$(HBASE_VERSION)/$(HBASE_TARBALL)
OPENTSDB_INSTALL := https://github.com/OpenTSDB/opentsdb/releases/download/v$(OPENTSDB_VERSION)/$(OPENTSDB_TARBALL)
HADOOP_INSTALL   := https://archive.apache.org/dist/hadoop/core/hadoop-$(HADOOP_VERSION)/$(HADOOP_TARBALL)

ZK_INSTALL       := http://archive.apache.org/dist/zookeeper/zookeeper-$(ZK_VERSION)/$(ZK_TARBALL)

all: hbase hadoop opentsdb zookeeper

hbase: build/$(HBASE_TARBALL)

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
	curl --fail -L -o $@ $(OPENTSDB_INSTALL)

build/$(ZK_TARBALL): | build
	curl --fail -o $@ $(ZK_INSTALL)

push:
	scp build/* zenpip.zendev.org:/home/pypiserver/packages

clean: 
	rm -rf build

# Copy tarballs to cache directory for development purposes
cache:
	mkdir -p ../cache
	cp build/* ../cache
