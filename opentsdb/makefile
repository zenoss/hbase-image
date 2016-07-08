HBASE_VERSION    := 1.1.4
OPENTSDB_VERSION := 2.2.0
HADOOP_VERSION   := 2.5.2
TARBALL          := opentsdb-$(OPENTSDB_VERSION)_hbase-$(HBASE_VERSION)_hadoop-$(HADOOP_VERSION).tar.gz
HBASE_TARBALL	 := hbase-$(HBASE_VERSION)-bin.tar.gz
OPENTSDB_TARBALL := opentsdb-$(OPENTSDB_VERSION).tar.gz
HADOOP_TARBALL   := hadoop-$(HADOOP_VERSION).tar.gz
HBASE_INSTALL    := https://archive.apache.org/dist/hbase/$(HBASE_VERSION)/$(HBASE_TARBALL)
OPENTSDB_INSTALL := https://github.com/OpenTSDB/opentsdb/releases/download/v$(OPENTSDB_VERSION)/$(OPENTSDB_TARBALL)
HADOOP_INSTALL   := https://archive.apache.org/dist/hadoop/core/hadoop-$(HADOOP_VERSION)/$(HADOOP_TARBALL)
ESAPI_INSTALL    := https://github.com/apache/hbase/blob/rel/$(HBASE_VERSION)/hbase-server/src/main/resources/ESAPI.properties
TARGET           := /mnt/pwd

.PHONY: default
default: $(TARBALL)

$(TARBALL): build build/$(HBASE_TARBALL) build/$(HADOOP_TARBALL) build/$(OPENTSDB_TARBALL) build/makefile build/ESAPI.properties
	docker run --rm -v $(PWD):$(TARGET) -w $(TARGET) maven:3.3.3-jdk-7 \
		/bin/bash -c "apt-get update && apt-get -y --force-yes install make autoconf patch && make tarball"

build:
	mkdir -p build

build/$(HADOOP_TARBALL):
	wget -O $@ $(HADOOP_INSTALL)

build/$(HBASE_TARBALL):
	wget -O $@ $(HBASE_INSTALL)

build/$(OPENTSDB_TARBALL):
	wget -O $@ $(OPENTSDB_INSTALL)

# There is a bug in Hbase 1.1.4 that causes this file to be missing.
build/ESAPI.properties:
	wget -O $@ $(ESAPI_INSTALL)

build/makefile:
	cp makefile build

.PHONY: tarball
tarball:
	mkdir -p /opt/zenoss/etc/supervisor
	tar -C /opt -xzf $(TARGET)/build/$(HBASE_TARBALL) --exclude src --exclude docs --exclude '*-tests.jar'
	ln -s /opt/hbase-$(HBASE_VERSION) /opt/hbase
	cp build/ESAPI.properties /opt/hbase/conf/
	tar -C /opt -xzf $(TARGET)/build/$(HADOOP_TARBALL) --exclude doc --exclude sources --exclude jdiff
	ln -s /opt/hadoop-$(HADOOP_VERSION) /opt/hadoop
	tar -C /opt -xzf $(TARGET)/build/$(OPENTSDB_TARBALL)
	ln -s /opt/opentsdb-$(OPENTSDB_VERSION) /opt/opentsdb
	cp /opt/hbase/lib/hadoop-client*.jar /opt/
	rm -f /opt/hbase/lib/hadoop-*
	mv /opt/hadoop-client*.jar /opt/hbase/lib/
	ln -s /opt/hadoop/share/hadoop/common/hadoop-*.jar /opt/hbase/lib/
	ln -s /opt/hadoop/share/hadoop/hdfs/hadoop-*.jar /opt/hbase/lib
	cp /opt/hadoop/share/hadoop/mapreduce/hadoop-*.jar /opt/hbase/lib/
	cp /opt/hadoop/share/hadoop/tools/lib/hadoop-*.jar /opt/hbase/lib/
	cp /opt/hadoop/share/hadoop/yarn/hadoop-*.jar /opt/hbase/lib/
	cd /opt/opentsdb-$(OPENTSDB_VERSION) && COMPRESSION=NONE HBASE_HOME=/opt/hbase-$(HBASE_VERSION) ./build.sh
	rm -rf /opt/opentsdb-$(OPENTSDB_VERSION)/build/gwt-unitCache /opt/opentsdb-$(OPENTSDB_VERSION)/build/third_party/gwt/gwt-dev-*.jar
	bash -c "rm -rf /opt/hadoop/share/hadoop/{httpfs,mapreduce,tools,yarn}"
	tar -czf $(TARBALL) /opt

clean:
	rm -rf $(TARBALL) build
