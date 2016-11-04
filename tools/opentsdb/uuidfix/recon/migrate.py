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
import logging
from multiprocessing import Pool
import os
import shutil
import signal
import time
import timer
import tsdbworker
import util


def args():
    parser = argparse.ArgumentParser(description="Migrate data from offline "
                                                 "tables to active tables")
    parser.add_argument("-s", "--srcconf", default="./opentsdb.conf",
                        help="opentsdb config file for source tables")
    parser.add_argument("-d", "--destconf",
                        default="/opt/opentsdb/build/opentsdb.conf",
                        help="opentsdb config file for destination tables")
    parser.add_argument("-m", "--metricfile", required=True,
                        help="file containing names of metrics to migrate")
    parser.add_argument("-o", "--outputdir", default="./out",
                        help="directory for output files")
    parser.add_argument("-b", "--bin-tsdb", dest='tsdbbin',
                        default="/opt/opentsdb/build/opentsdb/tsdb",
                        help="location of opentsdb binary (tsdb)")
    parser.add_argument("--logconfig", default="./logback.xml",
                        help="logback config file to use for opentsdb")
    parser.add_argument("--logconfig-destination", dest='logconfig_to',
                        default="/opt/opentsdb/src/logback.xml",
                        help="location where logback file will be copied"
                             " (including filename)")
    parser.add_argument("-n", "--num_workers", type=int, default=2,
                        help="number of worker processes to use")
    return parser.parse_args()


class MigrateMain(object):
    def __init__(self, opts):
        # self.logger = logging.getLogger('MigrateMain')
        self.opts = opts
        self.validate_options()
        self.logdir = os.path.join(self.opts.outputdir, "log")
        self.workdir = os.path.join(self.opts.outputdir, "work")
        self.errdir = os.path.join(self.opts.outputdir, "err")
        self.starttime = time.strftime('%Y%m%d-%H%M%S')
        for dir in (self.logdir, self.workdir, self.errdir):
            if not os.path.exists(dir):
                os.makedirs(dir)

    @property
    def logger(self):
        return logging.getLogger('migrate.MigrateMain')

    def validate_options(self):
        """
        validate command-line options. verify files exist,
        verify directories exist or can be created
        :return:
        """
        self.logger.debug("self.opts: %s", self.opts)
        errors = []
        #  files should exist
        files = [("-m/--metricfile", self.opts.metricfile),
                 ("-s/--srcconf", self.opts.srcconf),
                 ("-d/--destconf", self.opts.destconf),
                 ("--logconfig", self.opts.logconfig),
                 ("--logconfig-destination", self.opts.logconfig_to),
                 ("-b/--bin-tsdb", self.opts.tsdbbin)]
        for an, fn in files:
            if not os.path.isfile(fn):
                errors.append(IOError("argument {}: file {} does not exist."
                                      .format(an, fn)))
        # dirs should exist or we should be able to create them

        dirs = [("-o/--outputdir",self.opts.outputdir)]
                # ("-l/--logdir", self.opts.logdir),
                # ("-e/--errdir", self.opts.errdir),
                # ("-w/--workdir", self.opts.workdir)]
        for an, dir in dirs:
            if not os.path.exists(dir):
                try:
                    os.makedirs(dir)
                except os.error as e:
                    errors.append(IOError("argument {}: unable to find or "
                                          "create directory {}: {}"
                                          .format(an, dir, e)))
        # print messages and raise error if anything is not right
        if errors:
            self.logger.error("Improper arguments to command:")
            # print "Improper arguments to command:"
            for e in errors:
                self.logger.error("error: %s", e)
                # print "error: {}".format(e)
            exit(1)

    def run(self):
        """
        this is the 'main loop' for the program.
        """
        # Move log config file
        self.set_up_tsdb_logging()

        self.logger.info("##### starting %d workers at %s #####",
                         self.opts.num_workers, self.starttime)
        pool = Pool(processes=self.opts.num_workers)

        self.start_work()
        result = pool.imap_unordered(migrate_metric_worker, self.metric_workers())
        for r in result:
            self.metric_done(r[0], r[1])

        self.logger.info("Finished - got %d results in %f seconds. %d "
                         "successful, %d failed", self.resultcount,
                         self.t.ElapsedTime(), self.success, self.fail)
        self.write_failed_metrics()
        # print "Failed metrics: {}".format(self.fail_metrics)
        self.logger.info("Failed metrics: %s", self.fail_metrics)

    def start_work(self):
        self.resultcount = 0
        self.success = 0
        self.fail = 0
        self.fail_metrics = []

        self.metric_count = self.count_metric_names()
        self.t = timer.Timer(self.metric_count, "Metric")


    def metric_names(self):
        """
        Retrieve metric names for mapping
        :return: list of metric names
        """
        if self.opts.metricfile is None:
            return []
        with open(self.opts.metricfile, 'r') as f:
            return f.read().splitlines()

    def metric_workers(self):
        for metric in self.metric_names():
            yield tsdbworker.TSDBWorker(metric, self.opts.tsdbbin,
                                        self.opts.srcconf, self.opts.destconf,
                                        self.workdir, self.errdir,
                                        self.logdir, self.starttime)

    def count_metric_names(self):
        return sum(1 for i in self.metric_names())

    def metric_done(self, worker, result):
        self.logger.debug("metric_done for metric %s: result is %s", worker.metric_name, result)
        if result:
            self.success += 1
            self.log_success_metric(worker.metric_name)
        else:
            self.fail += 1
            self.fail_metrics.append(worker.metric_name)
        self.t.ItemsCompleted()
        self.resultcount += 1
        self.logger.info("%s: %s", worker.metric_name,
                         "OK" if result else "ERROR")
        self.logger.info("%s", self.t.GetPerfString())

    def write_failed_metrics(self):
        with open(os.path.join(self.logdir,
                               "failed_metrics-{}".format(self.starttime)),
                  "awt") as fm_file:
            fm_file.write("Failed metrics from run at {}:\n"
                          .format(self.starttime))
            for fm in self.fail_metrics:
                fm_file.write("{}\n".format(fm))

    def set_up_tsdb_logging(self):
        shutil.copy(self.opts.logconfig_to, "{}.bak".format(self.opts.logconfig_to))
        shutil.copy(self.opts.logconfig, self.opts.logconfig_to)

    def log_success_metric(self, metric_name):
        with open(os.path.join(self.logdir,
                               "success_metrics-{}".format(self.starttime)),
                  "awt") as gm_file:
            gm_file.write("{}\n".format(metric_name))


def migrate_metric_worker(args):
    """
    connect to opentsdb, read metric data, and write results to file
    :param args: WorkerArgs object for passing params to worker
    :return: boolean - True for success, False for failure
    """
    try:
        result = args.run()
    except Exception as e:
        logging.exception("Caught exception running thread")
    return args, result

def getlogfile(opts):
    dir = os.path.join(opts.outputdir, 'log')
    if not os.path.exists(dir):
        os.makedirs(dir)
    return os.path.join(dir, "migrate.log")

def setup_logging(logfile):
    logger = logging.getLogger('migrate')
    logger.setLevel(logging.DEBUG)
    fh = logging.FileHandler(logfile)
    fh.setLevel(logging.DEBUG)
    sh = logging.StreamHandler()
    sh.setLevel(logging.INFO)
    file_formatter = logging.Formatter('%(filename)s %(lineno)d - %(asctime)s - %(name)s - %(levelname)s - %(message)s')
    # file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    stream_formatter = logging.Formatter('%(levelname)s - %(message)s')
    # stream_formatter = logging.Formatter('%(filename)s %(lineno)d - %(levelname)s - %(message)s')
    fh.setFormatter(file_formatter)
    sh.setFormatter(stream_formatter)
    logger.addHandler(fh)
    logger.addHandler(sh)

if __name__ == '__main__':
    signal.signal(signal.SIGUSR1, util.handle_pdb)
    opts = args()
    logfile = getlogfile(opts)
    print 'logfile = {}'.format(logfile)
    setup_logging(logfile)
    MigrateMain(opts).run()
