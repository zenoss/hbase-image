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
import backoff
import collections
import glob
import gzip
import logging
import os
import shutil
from util import filename_safe
import itertools
from pipegen import gen_opener


def args():
    parser = argparse.ArgumentParser(
        description="Split larget data files and submit to opentsdb "
                    "with backoff.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-b", "--batchsize", type=int, default=100000)
    parser.add_argument("-d", "--destconf",
                        default="/opt/zenoss/etc/opentsdb/opentsdb.conf",
                        help="opentsdb config file for destination tables")
    parser.add_argument("-i", "--inputdir",
                        default="./reprocess.out/err",
                        help="directory from which to read input")
    parser.add_argument("-m", "--metricfile",
                        required=True, default="failed_metrics-20161107-141548",
                        help="file containing names of metrics to migrate")
    parser.add_argument("-o", "--outputdir",
                        default="./brp.out",
                        help="directory for output files")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="enable verbose logging")
    parser.add_argument("--logconfig", default="./logback.xml",
                        help="logback config file to use for opentsdb")
    parser.add_argument("--logconfig-destination", dest='logconfig_to',
                        default="/opt/opentsdb/src/logback.xml",
                        help="location where logback file will be copied"
                             " (including filename)")
    parser.add_argument("--tsdb-bin", dest="tsdbbin",
                        default="/opt/opentsdb/build/tsdb")
    return parser.parse_args()


def getlogfile(options):
    logdir = os.path.join(options.outputdir, 'log')
    if not os.path.exists(logdir):
        os.makedirs(logdir)
    return os.path.join(logdir, "rpbig.log")


def setup_logging(log_fn, verbose=False):
    logger = logging.getLogger('rpbig')
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


def uncompress_file(fn):
    newfn = fn.replace('.gz.gz', '.gz')
    with gzip.open(fn, 'rb') as f_in, open(newfn, 'wb') as f_out:
        shutil.copyfileobj(f_in, f_out)
    return newfn


class RPBigMain(object):
    def __init__(self, options):
        self.options = options
        self.work_dir = os.path.join(options.outputdir, 'work')
        self.err_dir = os.path.join(options.outputdir, 'err')
        self.log_dir = os.path.join(options.outputdir, 'log')
        for d in (self.work_dir, self.err_dir, self.log_dir):
            if not os.path.exists(d):
                os.makedirs(d)

    @property
    def logger(self):
        return logging.getLogger('rpbig.RPBigMain')

    def run(self):
        # for file in metrics
        with open(self.options.metricfilename) as f:
            for metric in f:
                self.uploadmetric(metric)
        pass

    def uploadmetric(self, metric):
        self.logger.info("uploading metric %s", metric)
        fn = self.get_metric_filename(metric)
        # break file into pieces (add argument for piece size)
        lines = gen_opener(fn)
        return self.upload_in_batches(lines, metric)

    def get_metric_filename(self, metric):
        fg = glob.glob("{}-dedup-*.gz.gz".format(filename_safe(metric)))
        # ^^^ TODO: This doesn't look quite right - may need to 'file-friendly'
        #  the metric name and/or include the source directory.
        if len(fg) != 1:
            self.logger.error("Unexpected file result(%s) for metric %s.",
                              fg, metric)
            return None
        fg_unzip = uncompress_file(fg[0])
        return fg_unzip

    def upload_in_batches(self, lines, metric):
        # TODO: maybe package results in named tuple for cleanness
        done = False
        seq = 0
        while not done:
            seq += 1
            batch = itertools.islice(lines, self.options.batchsize)
            self.upload_batch(batch, metric, seq) # TODO: read return and use to update stats


            # for each piece:
            # tsdb import (function decorated with backoff)
            # if success - log, delete interim files and move on
            # if failure - log, copy interm files to err and keep going

    def upload_batch(self, batch, metric, seq):
        """
        read lines from batch and write to a temp (gz) file.
        If line count > 0, call opentsdb (with backoff) to upload file.
        If line count == 0, return 0, True
        If upload is successful, delete tempfile, stdout/stderr and
        return line count, False
        If unsuccessful, copy file, stdout/stderr to temp storage, log error
        and return 0, False
        Idea: maybe return counts of lines read, lines stored (can then infer
        completion)
        :param batch:
        :param metric:
        :return: Line Count and indicator of lines attempted (False means lines
        read from generator, True means we're done)
        """
        Result = collections.namedtuple('Result', 'linecount success done')
        r = Result(0, False, False)
        workfile = self.get_working_filename(metric, seq)
        with gzip.open(workfile, 'wa') as wf:
            for line in batch:
                wf.write(line)
                r.linecount += 1

        if r.linecount > 0:
            success = self.tsdb_upload(workfile)
            if success:
                self.logger.debug("success uploading file {}".format(workfile))
            else:
                self.logger.warning("error uploading file {}".format(workfile))

        return r

    def get_working_filename(self, metric, seq=0):
        fn = os.path.join(self.work_dir,
                          '{}_{:06d}.data.gz'.format(metric, seq))
        return fn

    @backoff.backoff(maxtries=5, delay=1, backoff=2)
    def tsdb_upload(self, workfile):
        pass


if __name__ == '__main__':
    opts = args()
    logfile = getlogfile(opts)
    print 'logfile = {}'.format(logfile)
    setup_logging(logfile, opts.verbose)
    RPBigMain(opts).run()
