#hbase-image/download

This directory contains a makefile to assist in managing components used for 
building the hbase images.  It will download those components from source, 
and upload them to zenpip.

The flow of component artifacts is:
```
Source -> Local machine -> zenpip -> s3 -> Client build
```
This directory helps with the first two steps. Once the files are uploaded to 
zenpip, a Jenkins job copies them to the s3 mirror on an hourly basis. Clients 
making the hbase images will download from s3

## Downloading files

To download the files for hbase, hadoop, or opentsdb, use 
```
$ make hbase
```
replacing hbase with the appropriate target.  This command will download the 
relevant files to the build subdirectory

## Uploading files

To upload the files to the zenoss pip server, the command
```
$ make push
```
will upload all file in the build subdirectory to zenpip.  Note that you will 
need a login for the zenpip server.


