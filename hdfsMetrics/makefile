
PWD:=$(shell pwd)

# Note: $(BUILD_IMAGE) must be defined by calling process.

build:
	docker run \
	    --rm \
	    -v "$(PWD):/mnt/src" \
	    -v "$(HOME)/.m2:/root/.m2" \
	    -v "$(PWD)/maven_settings.xml:/usr/share/maven/conf/settings.xml" \
	    -w /mnt/src \
	    $(BUILD_IMAGE) \
	    mvn package

clean:
	docker run \
	    --rm \
	    -v "$(PWD):/mnt/src" \
	    -v "$(HOME)/.m2:/root/.m2" \
	    -v "$(PWD)/maven_settings.xml:/usr/share/maven/conf/settings.xml" \
	    -w /mnt/src \
	    $(BUILD_IMAGE) \
	    mvn clean

