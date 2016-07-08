HBASE_VERSION    := 1.1.4
OPENTSDB_VERSION := 2.2.0
HADOOP_VERSION   := 2.5.2
ZK_VERSION       := 3.4.5

VERSIONS_FILE    = ../../../versions
HBASE_IMAGE_VERSION    = $(shell awk /hbase/'{print $$2}' $(VERSIONS_FILE))
HDFS_IMAGE_VERSION     = $(shell awk /hdfs/'{print $$2}' $(VERSIONS_FILE))
OPENTSDB_IMAGE_VERSION = $(shell awk /opentsdb/'{print $$2}' $(VERSIONS_FILE))

HBASE_REPO?=zenoss/hbase
HDFS_REPO?=zenoss/hdfs
OPENTSDB_REPO?=zenoss/opentsdb

ZK_TARBALL := zookeeper-$(ZK_VERSION).tar.gz
ZK_URL     := http://archive.apache.org/dist/zookeeper/zookeeper-$(ZK_VERSION)/$(ZK_TARBALL)
HADOOP_TARBALL := opentsdb-$(OPENTSDB_VERSION)_hbase-$(HBASE_VERSION)_hadoop-$(HADOOP_VERSION).tar.gz
HADOOP_URL := https://zenoss-pip.s3.amazonaws.com/packages/$(HADOOP_TARBALL)

AUGMENTED_HADOOP_TARBALL := aug_$(HADOOP_TARBALL)
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
	wget -O $@ $(HADOOP_URL)

build/$(AUGMENTED_HADOOP_TARBALL): build/$(HADOOP_TARBALL) build/hdfsMetrics-1.0.jar | build
	docker run \
	    -v $(PWD):/mnt/pwd \
	    -w /mnt/pwd \
	    zenoss/rpmbuild:centos7 \
	    make docker_hadoop

docker_hadoop:
	tar -C/ -xzf build/$(HADOOP_TARBALL)
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
	tar -czf build/$(AUGMENTED_HADOOP_TARBALL) /opt /var/hdfs /var/hbase \
	    /usr/bin/run-hbase* /usr/bin/run-hdfs*

build/libhadoop.so: | build
	wget -O $@ https://zenoss-pip.s3.amazonaws.com/packages/libhadoop.so

image: build/hdfsMetrics-1.0.jar build/$(ZK_TARBALL) build/$(AUGMENTED_HADOOP_TARBALL) build/libhadoop.so
	docker build -t $(HBASE_REPO):$(HBASE_IMAGE_VERSION) .
	docker run \
	    -v $(PWD)/init_hdfs.sh:/tmp/init_hdfs.sh \
	    -v $(PWD)/hdfs-site.xml:/opt/hadoop/etc/hadoop/hdfs-site.xml \
	    -v $(PWD)/core-site.xml:/opt/hadoop/etc/hadoop/core-site.xml \
	    --name hadoop_build_$(DATE) \
	    $(HBASE_REPO):$(HBASE_IMAGE_VERSION) \
	    sh /tmp/init_hdfs.sh
	docker commit hadoop_build_$(DATE) $(HBASE_REPO):$(HBASE_IMAGE_VERSION)

tarballs: build/hdfsMetrics-1.0.jar build/$(ZK_TARBALL) build/$(AUGMENTED_HADOOP_TARBALL) build/libhadoop.so

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
