# Updating Libraries

One of the most common tasks in maintaining this repo is updating one or more 
of the component libraries.  (E.g., opentsdb, hbase, etc.)  This document 
explains the process for doing so.

## Steps

**1) Update the component version**

Update the relevant component version in [versions.mk](./versions.mk).  E.g., 
change *HADOOP_VERSION* from 2.5.2 to 2.5.3.  Normally you should not increment
image version on the develop branch, since this was incremented as part of the
release process.  

**2) Download the new components from source**

Please see these [instructions](./download/README.md#downloading-files) in the 
download folder for information about downloading components.  This action will download the 
version of the artifact indicated in versions.mk.

**3) Push the components to zenpip**

Again, see the [instructions](./download/README.md#uploading-files) in the download 
folder. This step will push the downloaded components to zenpip.

**4) Build the updated image**

In the root directory, run `make clean build`

