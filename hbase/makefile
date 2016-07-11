HBASE_VERSION    := 1.1.4
OPENTSDB_VERSION := 2.2.0
HADOOP_VERSION   := 2.5.2
ZK_VERSION       := 3.4.5

VERSIONS_FILE          = ./versions
HBASE_IMAGE_VERSION    = $(shell awk /hbase/'{print $$2}' $(VERSIONS_FILE))
HDFS_IMAGE_VERSION     = $(shell awk /hdfs/'{print $$2}' $(VERSIONS_FILE))
OPENTSDB_IMAGE_VERSION = $(shell awk /opentsdb/'{print $$2}' $(VERSIONS_FILE))

HBASE_REPO?=zenoss/hbase
HDFS_REPO?=zenoss/hdfs
OPENTSDB_REPO?=zenoss/opentsdb

HBASE_TARBALL	 := hbase-$(HBASE_VERSION)-bin.tar.gz
OPENTSDB_TARBALL := opentsdb-$(OPENTSDB_VERSION).tar.gz
HADOOP_TARBALL   := hadoop-$(HADOOP_VERSION).tar.gz
ZK_TARBALL       := zookeeper-$(ZK_VERSION).tar.gz

HBASE_INSTALL    := https://archive.apache.org/dist/hbase/$(HBASE_VERSION)/$(HBASE_TARBALL)
OPENTSDB_INSTALL := https://github.com/OpenTSDB/opentsdb/releases/download/v$(OPENTSDB_VERSION)/$(OPENTSDB_TARBALL)
HADOOP_INSTALL   := https://archive.apache.org/dist/hadoop/core/hadoop-$(HADOOP_VERSION)/$(HADOOP_TARBALL)
ESAPI_INSTALL    := https://github.com/apache/hbase/blob/rel/$(HBASE_VERSION)/hbase-server/src/main/resources/ESAPI.properties
ZK_URL           := http://archive.apache.org/dist/zookeeper/zookeeper-$(ZK_VERSION)/$(ZK_TARBALL)

AGGREGATED_TARBALL := opentsdb-$(OPENTSDB_VERSION)_hbase-$(HBASE_VERSION)_hadoop-$(HADOOP_VERSION).tar.gz

PWD:=$(shell pwd)
DATE:=$(shell date +%s)

default: image

build:
	mkdir -p build

build/hdfsMetrics-1.0.jar: | build
	docker run \
	    --rm \
	    -v $(PWD)/hdfsMetrics:/mnt/src/hdfsMetrics \
	    -v $(HOME)/.m2:/root/.m2 \
	    -v $(PWD)/maven_settings.xml:/usr/share/maven/conf/settings.xml \
	    -w /mnt/src/hdfsMetrics \
	    zenoss/rpmbuild:centos7 \
	    mvn package
	cp hdfsMetrics/target/hdfsMetrics-1.0-jar-with-dependencies.jar build/hdfsMetrics-1.0.jar

build/$(ZK_TARBALL): | build
	docker run \
	    -v $(PWD):/mnt/pwd \
	    -w /mnt/pwd \
	    zenoss/rpmbuild:centos7 \
	    make docker_zk

docker_zk:
	wget -O- $(ZK_URL) | tar -C/opt -xz \
	    --exclude contrib --exclude src --exclude docs --exclude dist-maven \
	    --exclude recipes --exclude CHANGES.txt --exclude build.xml
	ln -s /opt/zookeeper-$(ZK_VERSION) /opt/zookeeper
	cp run-zk.sh zookeeper-server /usr/bin
	chmod +x /usr/bin/run-zk.sh /usr/bin/zookeeper-server
	tar -czf build/$(ZK_TARBALL) /opt /usr/bin/run-zk.sh /usr/bin/zookeeper-server

build/$(HADOOP_TARBALL): | build
	wget -O $@ $(HADOOP_INSTALL)

build/$(HBASE_TARBALL): | build
	wget -O $@ $(HBASE_INSTALL)

build/$(OPENTSDB_TARBALL): | build
	wget -O $@ $(OPENTSDB_INSTALL)

# There is a bug in Hbase 1.1.4 that causes this file to be missing.
build/ESAPI.properties: | build
	wget -O $@ $(ESAPI_INSTALL)

build/$(AGGREGATED_TARBALL): build/$(HADOOP_TARBALL) build/$(HBASE_TARBALL) build/$(OPENTSDB_TARBALL) build/ESAPI.properties
	docker run \
	    -v $(PWD):/mnt/pwd \
	    -w /mnt/pwd \
	    maven:3.3.3-jdk-7 \
	    /bin/bash -c "apt-get update && apt-get -y --force-yes install make autoconf patch && make docker_hadoop"

docker_hadoop:
	mkdir -p /opt/zenoss/etc/supervisor
	tar -C /opt -xzf build/$(HBASE_TARBALL) --exclude src --exclude docs --exclude '*-tests.jar'
	ln -s /opt/hbase-$(HBASE_VERSION) /opt/hbase
	cp build/ESAPI.properties /opt/hbase/conf/
	tar -C /opt -xzf build/$(HADOOP_TARBALL) --exclude doc --exclude sources --exclude jdiff
	ln -s /opt/hadoop-$(HADOOP_VERSION) /opt/hadoop
	tar -C /opt -xzf build/$(OPENTSDB_TARBALL)
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
	#HBase files
	ln -s /opt/hadoop/lib/hdfsMetrics-1.0.jar /opt/hbase/lib/hdfsMetrics-1.0.jar
	mkdir -p /var/hbase
	mkdir -p /opt/hbase/logs /opt/zenoss/log /opt/zenoss/var
	sed -i -e 's/hbase.log.maxfilesize=256MB/hbase.log.maxfilesize=10MB/' /opt/hbase/conf/log4j.properties
	sed -i -e 's/hbase.log.maxbackupindex=20/hbase.log.maxbackupindex=10/' /opt/hbase/conf/log4j.properties
	cp run-hbase-standalone.sh run-hbase-master.sh run-hbase-regionserver.sh /usr/bin
	chmod a+x /usr/bin/run-hbase*
	#OpenTSDB files
	cp configure-hbase.sh check_hbase.py /opt/opentsdb
	cp opentsdb_service.conf /opt/zenoss/etc/supervisor/opentsdb_service.conf
	cp create_table_splits.rb create_table_splits.sh start-opentsdb.sh start-opentsdb-client.sh \
	    create-opentsdb-tables.sh set-opentsdb-table-ttl.sh opentsdb_watchdog.sh check_opentsdb.py \
	    /opt/opentsdb
	#HDFS files
	cp build/hdfsMetrics-1.0.jar /opt/hadoop/lib/hdfsMetrics-1.0.jar
	mkdir -p /var/hdfs/name /var/hdfs/data /var/hdfs/secondary
	cp run-hdfs-namenode run-hdfs-datanode run-hdfs-secondary-namenode /usr/bin
	chmod a+x /usr/bin/run-hdfs*
	tar -czf build/$(AGGREGATED_TARBALL) /opt /var/hdfs /var/hbase \
	    /usr/bin/run-hbase* /usr/bin/run-hdfs*

build/libhadoop.so: | build
	wget -O $@ https://zenoss-pip.s3.amazonaws.com/packages/libhadoop.so

image: build/hdfsMetrics-1.0.jar build/$(ZK_TARBALL) build/$(AGGREGATED_TARBALL) build/libhadoop.so
	docker build -t $(HBASE_REPO):$(HBASE_IMAGE_VERSION) .
	docker run \
	    -v $(PWD)/init_hdfs.sh:/tmp/init_hdfs.sh \
	    -v $(PWD)/hdfs-site.xml:/opt/hadoop/etc/hadoop/hdfs-site.xml \
	    -v $(PWD)/core-site.xml:/opt/hadoop/etc/hadoop/core-site.xml \
	    --name hadoop_build_$(DATE) \
	    $(HBASE_REPO):$(HBASE_IMAGE_VERSION) \
	    sh /tmp/init_hdfs.sh
	docker commit hadoop_build_$(DATE) $(HBASE_REPO):$(HBASE_IMAGE_VERSION)

tarballs: build/hdfsMetrics-1.0.jar build/$(ZK_TARBALL) build/$(AGGREGATED_TARBALL) build/libhadoop.so

# OpenTSDB image is just a different name for the hbase image
opentsdb:
	docker tag $(HBASE_REPO):$(HBASE_IMAGE_VERSION) $(OPENTSDB_REPO):$(OPENTSDB_IMAGE_VERSION)

# HDFS image is just a different name for the hbase image
hdfs:
	docker tag $(HBASE_REPO):$(HBASE_IMAGE_VERSION) $(HDFS_REPO):$(HDFS_IMAGE_VERSION)

push: default
	echo $(HOME)
	docker push $(HBASE_REPO):$(HBASE_IMAGE_VERSION)
	docker push $(HDFS_REPO):$(HDFS_IMAGE_VERSION)
	docker push $(OPENTSDB_REPO):$(OPENTSDB_IMAGE_VERSION)

clean:
	rm -rf build
	docker run \
	    --rm \
	    -v $(PWD)/hdfsMetrics:/mnt/src/hdfsMetrics \
	    -w /mnt/src/hdfsMetrics \
	    zenoss/rpmbuild:centos7 \
	    mvn clean
	@echo
