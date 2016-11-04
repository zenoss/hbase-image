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
import collections as c
import gzip
import os
import signal
import time

import util


def args():
    """
    standard argparse definition for command-line arguments
    :return: object with parsed argument values
    """
    parser = argparse.ArgumentParser(description="gather data to aid in "
                                     "fixing opentsdb corruption"
                                     " due to leaked UIDs")
    parser.add_argument("-m", "--metricfile",
                        help="File containing list of metrics to process")
    parser.add_argument("-v", "--verbose", help="Make output verbose",
                        action="store_true")
    parser.add_argument("-i", "--inputdir", default="./in")
    parser.add_argument("-o", "--outputdir", default="./out")
    return parser.parse_args()


class Step2Main(object):
    def __init__(self, opts):
        self.total_metrics = 0
        self.total_files = 0
        self.noguid_metrics = 0
        self.noguid_files = 0
        self.monoguid_metrics = 0
        self.monoguid_files = 0
        self.multiguid_metrics = 0
        self.multiguid_files = 0
        self.starttime = time.strftime('%Y%m%d-%H%M%S')
        self.opts = opts
        self.inputdir = self.opts.inputdir
        self.outputdir = self.opts.outputdir
        util.makedirectory(self.outputdir)
        self.metricfile = opts.metricfile

    def run_by_metric(self):
        for mf in self.get_metricfiles():
            self.total_files += 1
            self.get_metric_stats(mf)
        print "Processed {:8} files.   monoguid: {:8} noguid: {:8} " \
              "multiguid:{:8}".format(self.total_files, self.monoguid_files,
                                      self.noguid_files, self.multiguid_files)
        print "Processed {:8} metrics. monoguid: {:8} noguid: {:8} " \
              "multiguid:{:8}".format(self.total_metrics, self.monoguid_metrics,
                                      self.noguid_metrics,
                                      self.multiguid_metrics)

    def get_metricfiles(self):
        if self.metricfile:
            with open(self.metricfile) as f:
                for line in f.read().splitlines():
                    if os.path.isfile(line):
                        yield line
                    else:
                        inline = os.path.join(self.inputdir, line)
                        if os.path.isfile(inline):
                            yield inline
        else:
            for filename in os.listdir(self.inputdir):
                yield os.path.join(self.inputdir, filename)

    def get_metric_stats(self, metric_file):
        lc = 0
        mkt = MetricKeyTabulator()
        with gzip.open(metric_file) as f:
            for line in f.read().splitlines():
                lc += 1
                (metric, key, guid, count) = line.split()
                mkt.add(metric, key, guid, count)

        self.report_file(mkt, metric_file)

        if self.opts.verbose:
            print "{}: file: {} lines: {} metrics:{} metric-key pairs: {} " \
                  "has_multiguids: {} has_no_guids: {}"\
                .format(mkt.classify(), metric_file, lc, len(mkt.get_metrics()),
                        sum(1 for _ in mkt.get_mkg()), mkt.has_multiguid_mks(),
                        mkt.has_no_guids())

    def report_file(self, mkt, metric_file):
        self.total_metrics += len(mkt.get_metrics())
        cl = mkt.classify()
        if cl == "NOGUID":
            self.write_noguid(mkt, metric_file)
        elif cl == "MONOGUID":
            self.write_monoguid(mkt, metric_file)
        elif cl == "MULTIGUID":
            self.write_multiguid(mkt, metric_file)
        else:
            raise ValueError

    def write_noguid(self, mkt, metric_file):
        with open(self.get_output_filename("noguid_metrics"), 'awt') as f:
            for metric in mkt.get_metrics():
                self.noguid_metrics += 1
                f.write("{}\n".format(metric))
        with open(self.get_output_filename("noguid_files"), 'awt') as f:
            self.noguid_files += 1
            f.write("{}\n".format(metric_file))

    def write_monoguid(self, mkt, metric_file):
        with open(self.get_output_filename("monoguid_metrics"), 'awt') as f:
            for metric in mkt.get_metrics():
                self.monoguid_metrics += 1
                f.write("{}\n".format(metric))
        with open(self.get_output_filename("monoguid_files"), 'awt') as f:
            self.monoguid_files += 1
            f.write("{}\n".format(metric_file))

    def write_multiguid(self, mkt, metric_file):
        with open(self.get_output_filename("multiguid_metrics"), 'awt') as f:
            for metric in mkt.get_metrics():
                self.multiguid_metrics += 1
                f.write("{}\n".format(metric))
        with open(self.get_output_filename("multiguid_files"), 'awt') as f:
            self.multiguid_files += 1
            f.write("{}\n".format(metric_file))
        pass

    def get_output_filename(self, fn_str):
        return util.makefilename(self.outputdir, fn_str, self.starttime, ".txt")


class MetricKeyTabulator(object):
    def __init__(self):
        self.metrics = set()
        self.metric_paths = set()
        self.metric_path_guids = c.defaultdict(set)

    def add(self, metric, key, context_uuid, count):
        self.metrics.add(metric)
        self.metric_paths.add((metric, key))
        if context_uuid != "None":
            self.metric_path_guids[(metric, key)].add(context_uuid)

    def get_metrics(self):
        return self.metrics

    def get_mkg(self):
        return self.metric_path_guids

    def has_no_guids(self):
        for mk, guids in self.metric_path_guids.iteritems():
            if len(guids) > 0:
                return False
        return True

    def has_multiguid_mks(self):
        for mk, guids in self.metric_path_guids.iteritems():
            if len(guids) > 1:
                return True
        return False

    def get_multiguid_mks(self):
        for mk, guids in self.metric_path_guids.iteritems():
            if len(guids) > 1:
                yield(mk)

    def classify(self):
        noguids = self.has_no_guids()
        is_corrupted = self.has_multiguid_mks()
        if noguids:
            return "NOGUID"
        elif is_corrupted:
            return "MULTIGUID"
        else:
            return"MONOGUID"


if __name__ == '__main__':
    signal.signal(signal.SIGUSR1, util.handle_pdb)
    # Step2Main(args()).run()
    Step2Main(args()).run_by_metric()
