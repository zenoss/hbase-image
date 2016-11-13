#!/usr/bin/env python
##############################################################################
#
# Copyright (C) Zenoss, Inc. 2016, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
#
##############################################################################

"""
main program to collect metric data for remediation
of opentsdb issue at customer. It is intended to be run from a directory
bindmounted into a container (zenoss/opentsdb) and run inside the
container.
The program will iterate over list of metrics provided, connect to
opentsdb, and retrieve (via the scan command) the data for that metric.
It will iterate over the data  points, counting the number of times each
combination of contextUUID and key tag occurs, writing the totals out to
a file.
"""

import argparse
import gzip
import logging
from multiprocessing import Pool
import os
import signal
import time
from metricAccumulator import MetricAccumulator
import timer
import util
import datapoint as dp


def args():
    """
    standard argparse definition for command-line arguments
    :return: object with parsed argument values
    """
    parser = argparse.ArgumentParser(description="gather data to aid in " +
                                     "fixing opentsdb corruption" +
                                     " due to leaked UIDs")
    parser.add_argument("-m", "--metricfile",
                        help="File containing list of metrics to process")
    parser.add_argument("-v", "--verbose", help="Make output verbose",
                        action="store_true")
    parser.add_argument("-s", "--scriptdir", default=".",
                        help="path to directory where scripts reside")
    parser.add_argument("-w", "--workers", type=int, default=2,
                        help="number of worker containers")
    parser.add_argument("-d", "--datadir", default="./data/",
                        help="path to data directory")
    parser.add_argument("-c", "--tsdbconfig",
                        default="/opt/zenoss/etc/opentsdb/opentsdb.conf",
                        help="path to opentsdb config file")
    parser.add_argument("-b", "--tsdbbin", default="/opt/opentsdb//build//tsdb",
                        help="path to opentsdb binary file")
    return parser.parse_args()


class MapGuidsMain(object):
    """
    class to contain main program functionality
    """
    def __init__(self, options):
        """
        class initializer
        :param options:  argparse options
        :return: none
        """
        self.opts = options
        self.starttime = time.strftime('%Y%m%d-%H%M%S')
        self.setup_logging()
        self.datadir = self.opts.datadir
        util.makedirectory(self.datadir)
        self.outdir = os.path.join(self.datadir, "out")
        self.errdir = os.path.join(self.datadir, "err")


    def setup_logging(self):
        """
        Set up logging based on the class name and verbosity level
        """
        print "self.opts.datadir = {}".format(self.opts.datadir)
        log_filename = util.makefilename(self.opts.datadir, "mapguids",
                                         self.starttime, ".log")
        print("log_filename = {}".format(log_filename))
        if self.opts.verbose:
            logging.basicConfig(filename=log_filename, level=logging.DEBUG)
        else:
            logging.basicConfig(filename=log_filename, level=logging.INFO)


    def metric_names(self):
        """
        Retrieve metric names for mapping
        :return: list of metric names
        """
        logging.info("metric_names()")
        if self.opts.metricfile is None:
            return []
        with open(self.opts.metricfile, 'r') as f:
            return f.read().splitlines()

    def metric_args(self):
        #outfilename = util.makefilename(self.datadir, "metric_stats", self.starttime, ".gz")
        for metric in self.metric_names():
            # logging.info("yielding WorkerArgs() on metric %", metric)
            outfilename = util.makefilename(self.outdir, metric, self.starttime, "out.gz")
            yield WorkerArgs(metric, outfilename, self.opts.tsdbbin, self.opts.tsdbconfig, self.datadir, self.errdir)

    def count_metric_names(self):
        return sum(1 for i in self.metric_names())

    def metric_done(self, resultargs, result):
        if result:
            self.success += 1
        else:
            self.fail += 1
            self.fail_metrics.append(resultargs.metric)
        self.t.items_completed()
        self.resultcount += 1
        print "{}: {}\t{}".format(resultargs.metric, "OK" if result else "ERROR", self.t.perf_string())

    def start_work(self):
        self.resultcount = 0
        self.success = 0
        self.fail = 0
        self.fail_metrics = []

        self.metric_count = self.count_metric_names()
        self.t = timer.Timer(self.metric_count, "Metric")

    def write_failed_metrics(self):
        fm_filename = util.makefilename(self.outdir, "failed_metrics", self.starttime, ".txt" )

    def run(self):
        """
        this is the 'main loop' for the program.
        """
        logging.info("starting %d workers", self.opts.workers)
        pool = Pool(processes=self.opts.workers)

        self.start_work()
        result = pool.imap_unordered(map_metric_worker, self.metric_args())
        for r in result:
            self.metric_done(r[0], r[1])


        print "all done! got {} results in {} seconds. {} success and {} fail"\
            .format(self.resultcount, self.t.elapsed_time(), self.success,
                    self.fail)
        self.write_failed_metrics()
        print "Failed metrics: {}".format(self.fail_metrics)

class TSDBWorker(MetricAccumulator):
    def __init__(self, args):
        super(TSDBWorker, self).__init__()
        self.args = args
        self.metric = args.metric
        self.outfilename = args.outfile
        self.tsdb = args.tsdb
        self.datadir = args.datadir
        self.errdir = args.errdir

    def info(self, msg):
        print "INFO:{}".format(msg)

    def error(self, msg):
        print "ERROR: {}".format(msg)

    def run(self):
        # self.info("run")
        cmd = self.tsdb.call("scan", ["--import", "0", "sum", self.metric])
        result = False
        try:
            # self.info("running command {}".format(cmd))
            result = util.run_command(cmd, self.add_line, self.err_line)
        except util.ProcessFailedError as err:
            self.error("Process {} failed: {}".format(cmd, err))
            return False
        except ValueError as err:
            self.error("Caught ValueError running command {}: {}"
                       .format(cmd, err))
            return False
        self.write_results()
        return result

    def add_line(self, str):
        try:
            p = dp.Datapoint(str)
        except dp.ParseError as err:
            # ignore log message lines
            if ' INFO ' in str:
                return True
            # ignore warning messages, too
            if ' WARN ' in str:
                return True
            self.error("received ParseError for string: {}".format(str))
            return False
        self.add_point(p)
        return True

    def err_line(self, str):
        err_fn = util.makefilename(self.errdir, self.metric,
                                   time.strftime('%Y%m%d-%H%M%S'), ".err.gz")
        with gzip.open(err_fn, 'awt') as ef:
            ef.write(str)

    def write_results(self):
        # self.info("write_results()")
        lines_written = 0
        with gzip.open(self.outfilename, 'awt') as f:
            for mku, count in self.get_stats().iteritems():
                f.write("{} {} {} {}\n".format(mku[0], mku[1], mku[2], count))
                lines_written += 1

class WorkerArgs(object):
    def __init__(self, metric, outfile, tsdbbin, tsdbconfig, datadir, errdir):
        self.metric = metric
        self.tsdb = TSDBHelper(tsdbbin, tsdbconfig)
        self.outfile = outfile
        self.datadir = datadir
        self.errdir = errdir


class TSDBHelper(object):
    def __init__(self, tsdbbin, tsdbconf):
        self.tsdbbin = tsdbbin
        self.tsdbconf = tsdbconf

    def call(self, call, args):
        result = [self.tsdbbin, call, "--config", self.tsdbconf]
        result.extend(args)
        return result


def map_metric_worker(args):
        """
        connect to opentsdb, read metric data, and write results to file
        :param args: WorkerArgs object for passing params to worker
        :return: boolean - True for success, False for failure
        """
        w = TSDBWorker(args)
        result = w.run()
        return args, result

if __name__ == "__main__":
    signal.signal(signal.SIGUSR1, util.handle_pdb)
    MapGuidsMain(args()).run()
