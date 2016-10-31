#!/usr/bin/env python

##############################################################################
#
# Copyright (C) Zenoss, Inc. 2016, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
#
##############################################################################
import argparse
import ast
from collections import namedtuple
import gzip
import signal
import time
import util



def args():
    """
    standard argparse definition for command-line arguments
    :return: object with parsed argument values
    """
    parser = argparse.ArgumentParser(description="gather data to aid in " +
                                     "fixing opentsdb corruption" +
                                     " due to leaked UIDs")
    parser.add_argument("-s", "--statfile",
                        help="File with collected counts of metric keys " +
                        "guid combinations")
    parser.add_argument("-m", "--metricfile",
                        help="File containing list of metrics to process")
    parser.add_argument("-g", "--guidtablefile",
                        help="file containing zendmd guid table extract")
    parser.add_argument("-v", "--verbose", help="Make output verbose",
                        action="store_true")
    parser.add_argument("-d", "--datadir", default="./data/",
                        help="path to data directory")
    return parser.parse_args()

class Step2Main(object):
    def __init__(self, opts):
        self.statfile = opts.statfile
        self.starttime =  time.strftime('%Y%m%d-%H%M%S')
        # self.metrics_with_multiple_contextuuids = ()
        self.opts = opts
        self.guidtable = None
        self.datadir = self.opts.datadir
        util.makedirectory(self.datadir)
        
    def check_metric(self,metric):
        """
        Find all occurrences of metric in statfile.
        Keep list of guids for each metric/path(key) pair.
        If there are pairs with >1 guid per metric/key combo:
            look up guids in guidtablefile.
            If there is 1 match, save guid list and matched guid for use during migration
            If there is no match (but > 1 guid), metric cannot be remediated yet - further processing needed
            If there is >1 match for a metric/key combo, metric needs further processing before remediation.
        :param metric:
        :return:
        """
        lines = self.find_metric_in_file(metric, self.statfile)
        guids = {}
        multi_guids = False
        for line in lines:
            (name, key, guid, count) = line.split()

            if (name, key) in guids.keys():
                guids[(name,key)].append(guid)
                multi_guids = True
            else:
                guids[(name,key)] = (guid,)
        if multi_guids:
            for nk, glist in  guids.iteritems():
                matches = self.guidtable_lookup(glist) # TODO: fix this (or add interposing method) so it returns [([guid,...], path)] , or something like that.
                if len(matches) > 1:  # TODO: not quite right. Given above, figure out whether >1 GUID matches)
                    # TODO: womp womp - need to remediate. Write appropriate info to file.
                elif len(matches) == 1:
                    # TODO: success - GUID
                else:
                    # TODO: no matches found. Okay, if you have exactly 1 guid, but not otherwise.
        return


    def run(self):
        """
        :return:
        """
        d = {}
        input_line_count = 0
        with gzip.open(self.opts.statfile) as f:
            MK = namedtuple("MK", ["metric", "key"])
            for line in f:
                input_line_count += 1
                (m, k, contextUUID, count) = line.split()
                if k == "None":
                    k = None
                if contextUUID == "None":
                    contextUUID = None

                mk = MK(metric=m, key=k)
                if mk in d.keys():
                    d[mk].append(contextUUID)
                else:
                    d[mk] = (contextUUID,)
        print "d has {} entries.".format(len(d))
        migrate = []
        cleanup = []
        for entry, val in d.iteritems():
            #print "{}\t{}".format(repr(entry), repr(val))
            if len(val) == 1:
                migrate.append(entry)
            else:
                cleanup.append(entry)
        print "len(migrate): {}\tlen(cleanup): {}".format(len(migrate), len(cleanup))

        with gzip.open(util.makefilename(self.datadir,'ready_to_migrate',self.starttime, '.gz'),'wat') as f:
            for line in migrate:
                f.write(repr(line))

        with gzip.open(util.makefilename(self.datadir,'need_cleanup',self.starttime, '.gz'),'wat') as f:
            for line in cleanup:
                f.write(repr(line))


    def get_guidtable(self):
        if self.guidtable is None:
            self.guidtable = {}
            with gzip.open(self.opts.guidtablefile) as f:
                for line in f:
                    try:
                        (guid, path) = ast.literal_eval(line)
                        self.guidtable[guid] = path
                    except Exception, err:
                        print "error {} on line {}".format(err, line)
        return self.guidtable


    def lookup_context_uuid(self, uuid):
        if uuid in self.get_guidtable().keys():
            return self.get_guidtable()[uuid]
        return None

    def find_metric_in_file(self, metric, statfile):
        lines = []
        with gzip.open(statfile, 'r') as f:
            for line in f:
                fields = line.split()
                if len(fields) > 0 && fields[0] == metric:
                    lines.append(line)
        return lines

    def guidtable_lookup(self, glist):
        matches = []
        gt = self.get_guidtable()
        for guid in glist:
            if guid in glist.keys():
                matches.append((guid, glist[guid]))
        return matches

    def run_by_metric(self):
        pass


if __name__ == '__main__':
    signal.signal(signal.SIGUSR1, util.handle_pdb)
    # Step2Main(args()).run()
    Step2Main(args()).run_by_metric()