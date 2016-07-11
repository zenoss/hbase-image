# Steps to build new HDFS/HBase/Opentsdb Images for RM

This document was created in the RM 5.1.3/5.1.4 timeframe.
At that time, the zenoss/hbase, zenoss/hdfs and zenoss/opentsdb images for RM 
were simply different labels for the same image.

## Step 1 - Adjust the versions of the Opentsdb and/or Hbase software packages
Modify the version values for opentsdb, hadoop and/or hbase in the file
`services/repos/opentsdb/makefile`

Use the **EXACT** same version values in the file `services/repos/hbase/Dockerfile`

## Step 2 - Build the consolidated opentsdb/hbase/hadoop TAR file
```
# cd services/repos/opentsdb
# make
```

## Deveopmnent work flow
While iterating on the tar file, you can skip steps 3 and 4 and simply copy the 
consolidated TAR file to the hbase/build directory.  Continue to iterate with steps 
6 through 9 until satisfied, then return to steps 4 and 5.
```
# cd services/repos/hbase
# cp ../opentsdb/*.tar.gz build
```

## Step 3 - Copy the TAR file to zenpip.zendev.org
You may need help from someone who has credentials for zenpip to do this.
Here's an example - your mileage may vary depending on the versions of opentsdb/hbase
```
# scp ./opentsdb-2.2.0_hbase-0.98.6.tar.gz zenpip.zendev.org:/home/pypiserver/packages
```

## Step 4 - Mirror the TAR to S3
There is a cron job on zenpip which runs once an hour to mirror packages out to
storage on Amazon S3.  You can either wait for the cron job to run, or have
someone login to zenpip and push the file for you (i.e. a build engineer or
architect),

## Step 5 - Update the version numbers of the Docker images
Edit the `versions` file in the root of this source repo. Change both the
`hbase` and `opentsdb` values. Remember these are the versions of the docker images;
not the versions of hbase/opentsdb installed in the images.

## Step 6 - Build the docker images
```
# cd services/repos/hbase
# make
# make opentsdb hdfs
```
Note that the last command merely creates a tag for `zenoss/opentsdb` which
points to the newly created image.

## Step 7 - Update RM service definitions
In the `service` github repo, change the `hbase_VERSION`, `hdfs_VERSION`, and 
`opentsdb_VERSION` variables in the root level `makefile` to match the newly 
created images; i.e. the same values specified in Step 5 above.

## Step 8 - Test locally
Rebuild a devimg to generate service definitions that use the new images, and
deploy the new service definitions. Be sure to attach to the running containers
to verify they contain the versions you expect.
```
# zendev build devimg --clean
# zendev serviced -dx
```
## Step 9 - Modify Upgrade Scripts
Review each of the following scripts and make sure that they contain the proper
`SVC_USE` directive for both the hbase and opentsdb images:
* services/repos/zenoss5x/upgrade_templates/upgrade-core.txt.in
* services/repos/zenoss5x/upgrade_templates/upgrade-impact.txt.in
* services/repos/zenoss5x/upgrade_templates/upgrade-resmgr.txt.in
* services/repos/zenoss5x/upgrade_templates/upgrade-ucspm.txt.in

Here is an example:
```
SVC_USE zenoss/hbase:%HBASE_VERSION%
SVC_USE zenoss/opentsdb:%OPENTSDB_VERSION%
```
