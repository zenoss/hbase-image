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
ddrp module - stands for 'DeDupe and ReProcess'. This script was written for BBC
to reprocess metrics that failed because the 'tsdb scan ... --import ...'
command produced files that have duplicate data values for the same timestamp.
"""

import argparse
import logging
import os
from multiprocessing import Pool
import shutil
import time
import tsdbddworker
import timer


def args():
    parser = argparse.ArgumentParser(
        description="Find and eliminate duplicate lines in an opentsdb "
                    "data file.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-d", "--destconf",
                        default="/opt/zenoss/etc/opentsdb/opentsdb.conf",
                        help="opentsdb config file for destination tables")
    parser.add_argument("-m", "--metricfile",
                        required=True, default="failed_metrics-20161107-141548",
                        help="file containing names of metrics to migrate")
    parser.add_argument("-o", "--outputdir",
                        default="./reprocess.out",
                        help="directory for output files")
    parser.add_argument("-i", "--inputdir",
                        default="./out",
                        help="directory from which to read input")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="enable verbose logging")
    # parser.add_argument("-c", "--cleanup", action="store_true",
    #                     help="clean up input directory on success")
    parser.add_argument("-n", "--num_workers", type=int, default=2,
                        help="number of worker processes to use")
    parser.add_argument("--logconfig", default="./logback.xml",
                        help="logback config file to use for opentsdb")
    parser.add_argument("--logconfig-destination", dest='logconfig_to',
                        default="/opt/opentsdb/src/logback.xml",
                        help="location where logback file will be copied"
                             " (including filename)")
    parser.add_argument('-t', "--input-timestamp", dest="in_ts",
                        default="20161107-141548",
                        help="timestamp attached to input file metrics")
    parser.add_argument("--tsdb-bin", dest="tsdbbin",
                        default="/opt/opentsdb/build/tsdb")
    return parser.parse_args()


def getlogfile(options):
    logdir = os.path.join(options.outputdir, 'log')
    if not os.path.exists(logdir):
        os.makedirs(logdir)
    return os.path.join(logdir, "ddrp.log")


def setup_logging(log_fn, verbose=False):
    logger = logging.getLogger('ddrp')
    fh = logging.FileHandler(log_fn)
    sh = logging.StreamHandler()
    level = logging.INFO
    if verbose:
        level = logging.DEBUG
    logger.setLevel(level)
    fh.setLevel(level)
    sh.setLevel(level)
    if verbose:
        file_formatter = logging.Formatter(
            '%(filename)s %(lineno)d - %(asctime)s - %(name)s - '
            '%(levelname)s - %(message)s')
        stream_formatter = logging.Formatter(
            '%(filename)s %(lineno)d - %(levelname)s - %(message)s')
    else:
        file_formatter = logging.Formatter(
            '%(levelname)s - %(name)s - %(asctime)s - %(message)s')
        stream_formatter = logging.Formatter('%(levelname)s - %(message)s')
    fh.setFormatter(file_formatter)
    sh.setFormatter(stream_formatter)
    logger.addHandler(fh)
    logger.addHandler(sh)


class ResultCounter(object):
    def __init__(self, logdir, starttime):
        self.resultcount = 0
        self.success = 0
        self.fail = 0
        self.fail_metrics = []
        self.logdir = logdir
        self.starttime = starttime

    @property
    def success_fn(self):
        return os.path.join(self.logdir,
                            "success_metrics-{}".format(self.starttime))

    @property
    def fail_fn(self):
        return os.path.join(self.logdir,
                            "failed_metrics-{}".format(self.starttime))

    def log_success_metric(self, metric_name):
        with open(self.success_fn, "awt") as gm_file:
            gm_file.write("{}\n".format(metric_name))

    def log_fail_metric(self, metric_name):
        with open(self.fail_fn, "awt") as gm_file:
            gm_file.write("{}\n".format(metric_name))

    def reset(self):
        self.resultcount = 0
        self.success = 0
        self.fail = 0
        self.fail_metrics = []

    def failed(self, name):
        self.fail += 1
        self.fail_metrics.append(name)
        self.resultcount += 1

    def succeeded(self, name):
        self.success += 1
        self.log_success_metric(name)
        self.resultcount += 1


class DDRPMain(object):
    def __init__(self, options):
        self.opts = options
        self.t = timer.Timer(self.count_metric_names(), "Metric")
        self.starttime = time.strftime('%Y%m%d-%H%M%S')
        self.result_counter = ResultCounter(self.logdir, self.starttime)

    @property
    def logger(self):
        return logging.getLogger('ddrp.DDRPMain')

    @property
    def errdir(self):
        return os.path.join(self.opts.outputdir, "err")

    @property
    def logdir(self):
        return os.path.join(self.opts.outputdir, "log")

    @property
    def workdir(self):
        return os.path.join(self.opts.outputdir, "work")

    def count_metric_names(self):
        return sum(1 for _ in self.metric_names())

    def metric_done(self, worker, result):
        self.logger.debug("metric_done for metric %s: result is %s",
                          worker.metric_name, result)
        if result:
            self.result_counter.succeeded(worker.metric_name)
        else:
            self.result_counter.failed(worker.metric_name)
        self.t.items_completed()
        self.logger.info("%s: %s", worker.metric_name,
                         "OK" if result else "ERROR")
        self.logger.info("%s", self.t.perf_string())

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
            self.logger.debug("Yielding TSDBDDWorker(metric_name=%s, "
                              "tsdb_bin=%s, "
                              "in_ts=%s,"
                              "tsdb_config_dest=%s, "
                              "work_dir=%s, "
                              "err_dir=%s, "
                              "log_dir=%s, "
                              "src_dir=%s, "
                              "start_time=%s)",
                              metric,
                              self.opts.tsdbbin,
                              self.opts.in_ts,
                              self.opts.destconf,
                              self.workdir,
                              self.errdir,
                              self.logdir,
                              self.opts.inputdir,
                              self.starttime)
            yield tsdbddworker.TSDBDDWorker(metric_name=metric,
                                            tsdb_bin=self.opts.tsdbbin,
                                            in_ts=self.opts.in_ts,
                                            tsdb_config_dest=self.opts.destconf,
                                            work_dir=self.workdir,
                                            err_dir=self.errdir,
                                            log_dir=self.logdir,
                                            src_dir=self.opts.inputdir,
                                            start_time=self.starttime)

    def run(self):
        self.logger.debug("DEBUG LOGGING ENABLED")
        # Move log config file
        self.set_up_tsdb_logging()

        self.logger.info("##### starting %d workers at %s #####",
                         self.opts.num_workers, self.starttime)
        pool = Pool(processes=self.opts.num_workers)
        self.logger.debug("pool created")

        self.start_work()
        self.logger.debug("back from start_work()")
        result = pool.imap_unordered(ddrp_metric_worker, self.metric_workers())
        if not result:
            self.logger.warning("result from imap_unordered is None")
        for r in result:
            self.metric_done(r[0], r[1])

        self.logger.info("Finished - got %d results in %f seconds. %d "
                         "successful, %d failed",
                         self.result_counter.resultcount,
                         self.t.elapsed_time(), self.result_counter.success,
                         self.result_counter.fail)
        self.write_failed_metrics()
        self.logger.info("Failed metrics: %s", self.result_counter.fail_metrics)

    def set_up_tsdb_logging(self):
        shutil.copy(self.opts.logconfig_to,
                    "{}.bak".format(self.opts.logconfig_to))
        shutil.copy(self.opts.logconfig, self.opts.logconfig_to)

    def start_work(self):
        self.result_counter.reset()
        self.t.start()

    def write_failed_metrics(self):
        with open(os.path.join(self.logdir,
                               "failed_metrics-{}".format(self.starttime)),
                  "awt") as fm_file:
            fm_file.write("Failed metrics from run at {}:\n"
                          .format(self.starttime))
            for fm in self.result_counter.fail_metrics:
                fm_file.write("{}\n".format(fm))


def ddrp_metric_worker(job):
    """
    connect to opentsdb, read metric data, and write results to file
    :param job: TSDBDDWorker object for passing params to worker
    :return: boolean - True for success, False for failure
    """
    # noinspection PyBroadException
    result = False
    try:
        result = job.run()
    except Exception as e:
        logging.exception("Caught exception running thread: %", e)
    return job, result


if __name__ == '__main__':
    opts = args()
    logfile = getlogfile(opts)
    print 'logfile = {}'.format(logfile)
    setup_logging(logfile, opts.verbose)
    DDRPMain(opts).run()
