#!/bin/bash
##############################################################################
#
# Copyright (C) Zenoss, Inc. 2016, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
#
##############################################################################

# Create a script in the zenhub container to dump the guid table
serviced service attach zenhub su - zenoss -c "echo -e 'for entry in dmd.guid_table.items():\n print entry' > /tmp/table.dmd"

# Run the script, gzipping the output to a tmp file on the host.
serviced service attach zenhub su - zenoss -c "zendmd --script /tmp/table.dmd" | gzip > ./guidtable.gz
