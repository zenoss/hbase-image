include ../versions.mk

ZENPIP := https://zenoss-pip.s3.amazonaws.com/packages

# Internal zenpip server
# ZENPIP := http://zenpip.zendev.org/packages

HBASE_REPO?=zenoss/hbase
HDFS_REPO?=zenoss/hdfs
OPENTSDB_REPO?=zenoss/opentsdb

AGGREGATED_TARBALL := opentsdb-$(OPENTSDB_VERSION)_hbase-$(HBASE_VERSION)_hadoop-$(HADOOP_VERSION).tar.gz

PWD:=$(shell pwd)
DATE:=$(shell date +%s)

build: hbase hdfs opentsdb

BUILD_DIR:
	mkdir -p build

stage:
	mkdir -p stage

stage/hdfsMetrics-1.0.jar: | stage
	docker run \
	    --rm \
	    -v $(PWD)/hdfsMetrics:/mnt/src/hdfsMetrics \
	    -v $(HOME)/.m2:/root/.m2 \
	    -v $(PWD)/maven_settings.xml:/usr/share/maven/conf/settings.xml \
	    -w /mnt/src/hdfsMetrics \
	    zenoss/rpmbuild:centos7 \
	    mvn package
	cp hdfsMetrics/target/hdfsMetrics-1.0-jar-with-dependencies.jar $@

stage/$(ZK_TARBALL): | stage
	wget -O $@ $(ZENPIP)/$(@F)

build/$(ZK_TARBALL): stage/$(ZK_TARBALL) | BUILD_DIR
	docker run --rm \
	    -v $(PWD)/..:/mnt/pwd \
	    -w /mnt/pwd/image \
	    zenoss/rpmbuild:centos7 \
	    make docker_zk

docker_zk:
	tar -C/opt -xzf stage/$(ZK_TARBALL) \
	    --exclude contrib --exclude src --exclude docs --exclude dist-maven \
	    --exclude recipes --exclude CHANGES.txt --exclude build.xml
	ln -s /opt/zookeeper-$(ZK_VERSION) /opt/zookeeper
	cp run-zk.sh zookeeper-server /usr/bin
	chmod +x /usr/bin/run-zk.sh /usr/bin/zookeeper-server
	tar -czf build/$(ZK_TARBALL) /opt /usr/bin/run-zk.sh /usr/bin/zookeeper-server

stage/$(HADOOP_TARBALL): | stage
	wget -O $@ $(ZENPIP)/$(@F)

stage/$(HBASE_TARBALL): | stage
	wget -O $@ $(ZENPIP)/$(@F)

stage/$(OPENTSDB_TARBALL): | stage
	wget -O $@ $(ZENPIP)/$(@F)

stage/libhadoop.so: | stage
	wget -O $@ $(ZENPIP)/$(@F)

# There is a bug in Hbase 1.1.4 that causes this file to be missing.
stage/$(ESAPI_FILE): | stage
	wget -O $@ $(ZENPIP)/$(@F)

build/$(AGGREGATED_TARBALL): stage/$(HADOOP_TARBALL) stage/$(HBASE_TARBALL) stage/$(OPENTSDB_TARBALL) stage/$(ESAPI_FILE) stage/hdfsMetrics-1.0.jar
	docker run --rm \
	    -v $(PWD)/..:/mnt/pwd \
	    -w /mnt/pwd/image \
	    maven:3.3.3-jdk-7 \
	    /bin/bash -c "apt-get update && apt-get -y --force-yes install make autoconf patch && make docker_hadoop"

docker_hadoop:
	mkdir -p /opt/zenoss/etc/supervisor
	tar -C /opt -xzf stage/$(HBASE_TARBALL) --exclude src --exclude docs --exclude '*-tests.jar'
	ln -s /opt/hbase-$(HBASE_VERSION) /opt/hbase
	cp stage/$(ESAPI_FILE) /opt/hbase/conf/ESAPI.properties
	tar -C /opt -xzf stage/$(HADOOP_TARBALL) --exclude doc --exclude sources --exclude jdiff
	ln -s /opt/hadoop-$(HADOOP_VERSION) /opt/hadoop
	tar -C /opt -xzf stage/$(OPENTSDB_TARBALL)
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
	cp stage/hdfsMetrics-1.0.jar /opt/hadoop/lib/hdfsMetrics-1.0.jar
	mkdir -p /var/hdfs/name /var/hdfs/data /var/hdfs/secondary
	cp run-hdfs-namenode run-hdfs-datanode run-hdfs-secondary-namenode /usr/bin
	chmod a+x /usr/bin/run-hdfs*
	tar -czf build/$(AGGREGATED_TARBALL) /opt /var/hdfs /var/hbase \
	    /usr/bin/run-hbase* /usr/bin/run-hdfs*

build/libhadoop.so: stage/libhadoop.so | BUILD_DIR
	cp -p $< $@ 

build/Dockerfile: Dockerfile | BUILD_DIR
	cp $< $@

hbase: build/$(ZK_TARBALL) build/$(AGGREGATED_TARBALL) build/libhadoop.so build/Dockerfile
	docker build -t $(HBASE_REPO):$(HBASE_IMAGE_VERSION) build
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
