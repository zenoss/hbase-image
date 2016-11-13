#!/usr/bin/env bash

##############################################################################
#
# Copyright (C) Zenoss, Inc. 2016, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
#
##############################################################################

echo "fakeopentsdb" $@

function hasdupes()
{
    LINES=$(zcat ${FILENAME} | cut -d' ' -f1-2,4- | sort | uniq -d)
    if [[ -z $LINES ]]
    then
        return 0
    fi
    return 1
}

FILENAME=$5
hasdupes
exit  $?
