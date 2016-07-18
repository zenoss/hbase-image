# hdfs-image/makefile
#
#   This makefile is responsible for building the hbase, hdfs, ond opentsdb 
# images for the Zenoss service. 
#
#   The output of running with the 'build' target will be the three images.
# As part of the process, several caches are created: the 'cache' directory
# containing a cache of non-volatile source files downloaded from zenpip, and
# the 'build' directory, containing volatile intermediate files based on the 
# cached files.  The 'cache' and 'build' directories are created via "order-only"
# prerequisites, described below.  
#
# A 'sentinel' directoy is created with files which track the presence of and 
# modification date of the three images.  These files are use to determine whether
# a given image needs to be rebuilt.
#
# Several of the targets invoke docker to create a tarball containing the results
# of some operations (such as installing software).
#
# Order-only prerequisites: This is discussed here as many are not familiar with 
# them. These prerequisites indicate that the prereq should be built if it not 
# present but that the date on the prereq should not be used to trigger.  
# Order-only prereqs are used to ensure that a directory is created before any
# files are placed in it.  All prereqs following the pipe operater (|) in the list
# of prereqs are order-only.  See 
#   https://www.gnu.org/software/make/manual/html_node/Prerequisite-Types.html


include versions.mk

# Image used for builds in docker containers.
# Note that this variable is exported for hdfsMetrics recursive make invocations.
export BUILD_IMAGE := zenoss/build-tools:0.0.3

ZENPIP := https://zenoss-pip.s3.amazonaws.com/packages
# Internal zenpip server, in case you don't want to wait for s3
# ZENPIP := http://zenpip.zendev.org/packages

HBASE_REPO?=zenoss/hbase
HDFS_REPO?=zenoss/hdfs
OPENTSDB_REPO?=zenoss/opentsdb

HBASE_IMAGE    := $(HBASE_REPO):$(IMAGE_VERSION)
HDFS_IMAGE     := $(HDFS_REPO):$(IMAGE_VERSION)
OPENTSDB_IMAGE := $(OPENTSDB_REPO):$(IMAGE_VERSION)

# Initialize the hbase, hdfs, and opentsdb placeholder files. These files match 
# the existence and date of the corresponding images for the make process to 
# use in determining when a file is out of date.  Using the := operator ensures 
# that each of these commands will execute exactly once when make is started.
DUMMY := $(shell mkdir -p -m 0777 sentinel)
DUMMY := $(shell ./set_date_from_image $(HBASE_IMAGE) sentinel/hbase)
DUMMY := $(shell ./set_date_from_image $(HDFS_IMAGE) sentinel/hdfs)
DUMMY := $(shell ./set_date_from_image $(OPENTSDB_IMAGE) sentinel/opentsdb)

AGGREGATED_TARBALL := opentsdb-$(OPENTSDB_VERSION)_hbase-$(HBASE_VERSION)_hadoop-$(HADOOP_VERSION).tar.gz

PWD:=$(shell pwd)
DATE:=$(shell date +%s)

.PHONY: build hbase hdfs opentsdb push clean release verifyVersion verifyImage

build: hbase hdfs opentsdb

hbase: sentinel/hbase

hdfs: sentinel/hdfs

opentsdb: sentinel/opentsdb

BUILD_DIR:
	mkdir -p build

# This is a directory for caching stable downloaded files.  (I.e., files
# whose contents are expected to never change, typically versioned files.)
# As a cache, this directory is NOT cleared by a 'make clean' operation, 
# in a similar fashion to the files cached by Maven.
cache:
	mkdir -p cache

cache/%: | cache
	curl --fail -o $@ $(ZENPIP)/$(@F)

# Note: the version in the hdfsMetrics pom.xml *must* match $HDFSMETRICS_VERSION
cache/$(HDFSMETRICS_JAR): | cache
	cd hdfsMetrics; make build
	cp hdfsMetrics/target/hdfsMetrics-$(HDFSMETRICS_VERSION)-jar-with-dependencies.jar $@

build/$(ZK_TARBALL): cache/$(ZK_TARBALL) | BUILD_DIR
	docker run --rm \
	    -v "$(PWD):/mnt/pwd" \
	    -w /mnt/pwd/ \
	    $(BUILD_IMAGE) \
	    make docker_zk

# The docker_zk target is intended to be run only within a docker container
# as a result of running the recipe for the ZK_TARBALL.  It installs Zookeeper, 
# then archives the resulting files.
docker_zk:
	ps -p1 -o args= | grep $@     # Ensure we are building this target in a container
	tar -C/opt -xzf cache/$(ZK_TARBALL) \
	    --exclude contrib --exclude src --exclude docs --exclude dist-maven \
	    --exclude recipes --exclude CHANGES.txt --exclude build.xml
	ln -s /opt/zookeeper-$(ZK_VERSION) /opt/zookeeper
	cd src/zookeeper; cp run-zk.sh zookeeper-server /usr/bin
	chmod +x /usr/bin/run-zk.sh /usr/bin/zookeeper-server
	tar -czf build/$(ZK_TARBALL) /opt /usr/bin/run-zk.sh /usr/bin/zookeeper-server

build/$(AGGREGATED_TARBALL): cache/$(HADOOP_TARBALL) cache/$(HBASE_TARBALL) cache/$(OPENTSDB_TARBALL) cache/$(ESAPI_FILE) cache/$(HDFSMETRICS_JAR) | BUILD_DIR
	docker run --rm \
	    -v "$(PWD):/mnt/pwd" \
	    -w /mnt/pwd \
	    $(BUILD_IMAGE) \
	    make docker_aggregated

# The docker_aggregated target is intended to be run only within a docker container
# as a result of running the recipe for the AGGREGATED_TARBALL.  It installs Hadoop, HBase, 
# and OpenTSDB, then archives the resulting files.
docker_aggregated:
	ps -p1 -o args= | grep $@     # Ensure we are building this target in a container
	mkdir -p /opt/zenoss/etc/supervisor
	tar -C /opt -xzf cache/$(HBASE_TARBALL) --exclude src --exclude docs --exclude '*-tests.jar'
	ln -s /opt/hbase-$(HBASE_VERSION) /opt/hbase
	cp cache/$(ESAPI_FILE) /opt/hbase/conf/ESAPI.properties
	tar -C /opt -xzf cache/$(HADOOP_TARBALL) --exclude doc --exclude sources --exclude jdiff
	ln -s /opt/hadoop-$(HADOOP_VERSION) /opt/hadoop
	tar -C /opt -xzf cache/$(OPENTSDB_TARBALL)
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
	ln -s /opt/hadoop/lib/$(HDFSMETRICS_JAR) /opt/hbase/lib/$(HDFSMETRICS_JAR)
	mkdir -p /var/hbase
	mkdir -p /opt/hbase/logs /opt/zenoss/log /opt/zenoss/var
	mkdir -p /opt/hbase/lib/native/Linux-amd64-64
	ln -s /opt/hadoop/lib/native/libhadoop.so /opt/hbase/lib/native/Linux-amd64-64
	sed -i -e 's/hbase.log.maxfilesize=256MB/hbase.log.maxfilesize=10MB/' /opt/hbase/conf/log4j.properties
	sed -i -e 's/hbase.log.maxbackupindex=20/hbase.log.maxbackupindex=10/' /opt/hbase/conf/log4j.properties
	cd src/hbase; cp run-hbase-standalone.sh run-hbase-master.sh run-hbase-regionserver.sh /usr/bin
	chmod a+x /usr/bin/run-hbase*
	#OpenTSDB files
	cd src/opentsdb; cp configure-hbase.sh check_hbase.py /opt/opentsdb
	cd src/opentsdb; cp opentsdb_service.conf /opt/zenoss/etc/supervisor/opentsdb_service.conf
	cd src/opentsdb; cp create_table_splits.rb create_table_splits.sh start-opentsdb.sh start-opentsdb-client.sh \
	    create-opentsdb-tables.sh set-opentsdb-table-ttl.sh opentsdb_watchdog.sh check_opentsdb.py \
	    /opt/opentsdb
	#HDFS files
	cp cache/$(HDFSMETRICS_JAR) /opt/hadoop/lib/$(HDFSMETRICS_JAR)
	mkdir -p /var/hdfs/name /var/hdfs/data /var/hdfs/secondary
	cd src/hdfs; cp run-hdfs-namenode run-hdfs-datanode run-hdfs-secondary-namenode /usr/bin
	chmod a+x /usr/bin/run-hdfs*
	tar -czf build/$(AGGREGATED_TARBALL) /opt /var/hdfs /var/hbase \
	    /usr/bin/run-hbase* /usr/bin/run-hdfs*

build/Dockerfile: Dockerfile.in | BUILD_DIR
	sed $< >$@ \
	    -e 's~{{BASE_IMAGE}}~$(BASE_IMAGE)~' \
	    -e 's~{{HADOOP_VERSION}}~$(HADOOP_VERSION)~' \
	    -e 's~{{HBASE_VERSION}}~$(HBASE_VERSION)~' \
	    -e 's~{{OPENTSDB_VERSION}}~$(OPENTSDB_VERSION)~' \
	    -e 's~{{ZK_VERSION}}~$(ZK_VERSION)~' \


# Build the hbase image and initialize HDFS
sentinel/hbase: build/$(ZK_TARBALL) build/$(AGGREGATED_TARBALL) build/Dockerfile
	docker build -t $(HBASE_IMAGE) build
	docker run \
	    -v "$(PWD)/src/init_hdfs/init_hdfs.sh:/tmp/init_hdfs.sh" \
	    -v "$(PWD)/src/init_hdfs/hdfs-site.xml:/opt/hadoop/etc/hadoop/hdfs-site.xml" \
	    -v "$(PWD)/src/init_hdfs/core-site.xml:/opt/hadoop/etc/hadoop/core-site.xml" \
	    --name hadoop_build_$(DATE) \
	    $(HBASE_IMAGE) \
	    sh /tmp/init_hdfs.sh
	docker commit hadoop_build_$(DATE) $(HBASE_IMAGE)
	@./set_date_from_image $(HBASE_IMAGE) $@

# OpenTSDB image is just a different name for the hbase image
sentinel/opentsdb: sentinel/hbase
	docker tag $(HBASE_IMAGE) $(OPENTSDB_IMAGE)
	@./set_date_from_image $(HBASE_IMAGE) $@

# HDFS image is just a different name for the hbase image
sentinel/hdfs: sentinel/hbase
	docker tag $(HBASE_IMAGE) $(HDFS_IMAGE)
	@./set_date_from_image $(HBASE_IMAGE) $@

push:
	docker push $(HBASE_IMAGE)
	docker push $(HDFS_IMAGE)
	docker push $(OPENTSDB_IMAGE)

clean:
	-docker rmi $(HBASE_IMAGE) $(OPENTSDB_IMAGE) $(HDFS_IMAGE)
	rm -rf build sentinel
	cd hdfsMetrics; make clean

# Generate a make failure if the VERSION string contains "-<some letters>"
verifyVersion:
	@./verifyVersion.sh $(IMAGE_VERSION)

# Generate a make failure if the image(s) already exist
verifyImage:
	@./verifyImage.sh $(HBASE_REPO) $(IMAGE_VERSION)
	@./verifyImage.sh $(HDFS_REPO) $(IMAGE_VERSION)
	@./verifyImage.sh $(OPENTSDB_REPO) $(IMAGE_VERSION)

# Do not release if the image version is invalid
# This target is intended for use when trying to build/publish images from the master branch
release: verifyVersion verifyImage clean build push

