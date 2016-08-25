# hbase-image 

Centos image with hdfs, hbase, and opentsdb installed. A single docker image with three aliases is created from this project: 
_zenoss/hbase_, _zenoss/hdfs_, and _zenoss/opentsdb_.

The _download_ subdirectory contains facilities for managing the third-party components from which these images are built.
Please see the [README file](./download/README.md) for more details.

# Building

To buid a dev images for testing locally, use 
  * `git checkout develop` 
  * `git pull origin develop`
  * `make clean build`

The result should be a set of `X.X.X-dev` images in your local docker repo (e.g. `1.0.0-dev`).   If you need to make changes, create
a feature branch like you would for any other kind of change, modify the image definition as necessary, use `make clean build` to
build an image and then test it as necessary.   Once you have finished your local testing, commit your changes, push them,
and create a pull-request as you would normally. A Jenkins PR build will be started to verify that your changes will build in
a Jenkins environment.

One of the most common changes in this repo is updating the version of the component libraries.  Instructions for doing so can be 
found [here](./updating-libraries.md).

# Releasing

Use git flow to release a version to the `master` branch.

The image version is defined in [versions.mk](./versions.mk).

For Zenoss employees, the details on using git-flow to release a version is documented on the Zenoss Engineering [web site](https://sites.google.com/a/zenoss.com/engineering/home/faq/developer-patterns/using-git-flow).
 After the git flow process is complete, a jenkins job can be triggered manually to build and 
 publish the images to docker hub. 
