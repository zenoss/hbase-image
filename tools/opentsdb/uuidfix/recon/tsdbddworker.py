#!/usr/bin/env python

##############################################################################
#
# Copyright (C) Zenoss, Inc. 2016, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
#
##############################################################################
import gzip
import logging
import os
import shutil
import subprocess
import finddupes

import util


class TSDBDDWorker(object):
    def __init__(self, metric_name=None, tsdb_bin=None, in_ts=None,
                 tsdb_config_dest=None, src_dir=None, work_dir=".",
                 err_dir=None, log_dir=None, start_time=None, logger=None):
        self.parent_logger = logger
        self.metric_name = metric_name
        self.tsdb_bin = tsdb_bin
        self.in_ts = in_ts
        self.tsdb_config_dest = tsdb_config_dest
        self.work_dir = work_dir
        self.err_dir = err_dir
        self.log_dir = log_dir
        self.src_dir = src_dir
        self.start_time = start_time
        for d in (self.work_dir, self.err_dir, self.log_dir, self.src_dir):
            if not os.path.exists(d):
                os.makedirs(d)

    @property
    def logger(self):
        return logging.getLogger('ddrp.TSDBDDWorker')

    def get_out_file_name(self, operation):
        return "{}-{}-{}.out".format(util.filename_safe(self.metric_name),
                                     self.start_time, operation)

    def get_err_file_name(self, operation):
        return "{}-{}-{}.err".format(util.filename_safe(self.metric_name),
                                     self.start_time, operation)

    def get_input_file_name(self):
        return "{}-{}-export.out.gz".format(
            util.filename_safe(self.metric_name), self.in_ts)

    def get_work_file_name(self):
        return "{}-dedup-{}.gz".format(util.filename_safe(self.metric_name),
                                       self.start_time)

    def get_input_file_full_name(self):
        return os.path.join(self.src_dir, "err", self.get_input_file_name())

    def get_out_file_full_name(self, operation):
        return os.path.join(self.work_dir, self.get_out_file_name(operation))

    def get_err_file_full_name(self, operation):
        return os.path.join(self.work_dir, self.get_err_file_name(operation))

    def get_work_file_full_name(self):
        return os.path.join(self.work_dir, self.get_work_file_name())

    def archive_file(self, orig_file, to, compress=True):
        self.logger.debug("moving %s to %s", orig_file, self.err_dir)
        if compress:
            source_fn = os.path.basename(orig_file)
            with open(orig_file, 'rb') as f_in, gzip.open(
                    os.path.join(self.err_dir, "{}.gz".format(source_fn)),
                    'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
            os.remove(orig_file)
        else:
            shutil.move(orig_file, to)

    def dedupe_and_reload(self):
        self.logger.info("removing duplicate values from metric %s",
                         self.metric_name)
        if self.dedupe_metric():
            self.logger.info("importing metric %s", self.metric_name)
            status = self.import_metric()
        else:
            self.logger.info("error removing duplicate values from metric %s",
                             self.metric_name)
            return False
        return status

    def dedupe_metric(self):
        f_in = self.get_input_file_full_name()
        fn_work = self.get_work_file_full_name()
        self.logger.debug("dedupe_metric(). f_in = %s fn_work = %s", f_in,
                          fn_work)
        inlines = gzip.open(f_in)
        self.logger.debug("calling finddupes.dedupe()")
        outlines = finddupes.dedupe(inlines, self.logger)
        self.logger.debug("opening work file and writing lines")
        with gzip.open(fn_work, "wa") as f_work:
            for ol in outlines:
                f_work.write(ol)
        self.logger.debug("done. returning True")
        return True

    def import_metric(self):
        datafile = self.get_work_file_full_name()
        cmd = [self.tsdb_bin, "import", "--config", self.tsdb_config_dest,
               datafile]
        err_file = self.get_err_file_full_name("import")
        out_file = self.get_out_file_full_name("import")
        status = self.run_command(cmd, "import")

        if status:
            # TODO: check err_file (and stdout?) for ERROR
            self.logger.debug("removing %s", err_file)
            os.remove(err_file)
            self.logger.debug("removing %s", out_file)
            os.remove(out_file)
            self.logger.debug("removing %s", datafile)
            os.remove(datafile)
        else:
            self.logger.info("error importing metric %s", self.metric_name)
            # no success, move out/err files to error directory
            self.archive_file(err_file, self.err_dir)
            self.archive_file(out_file, self.err_dir)
            self.archive_file(datafile, self.err_dir)
        return status

    def log_success_metric(self, metric_name):
        with open(os.path.join(self.log_dir,
                               "success_metrics-{}".format(self.start_time)),
                  "awt") as gm_file:
            gm_file.write("{}\n".format(metric_name))

    def run_command(self, cmd, operation):
        stdout_file = self.get_out_file_full_name(operation)
        stderr_file = self.get_err_file_full_name(operation)
        with open(stdout_file, 'awt') as out_f, \
                open(stderr_file, 'awt') as err_f:
            p = subprocess.Popen(cmd, stdout=out_f, stderr=err_f)
            p.wait()
            return p.returncode == 0

    def run(self):
        self.logger.debug("run() for worker with metric %s", self.metric_name)
        result = False
        try:
            result = self.dedupe_and_reload()
        except Exception as e:
            self.logger.exception("exception raised in migrate_data for metric "
                                  "%s: %s",self.metric_name, e)
        return result


if __name__ == '__main__':
    w = TSDBDDWorker(
        metric_name="mon541.back.mgmt.bc.localiostat_avgqu-sz",
        tsdb_bin="./fakeopentsdb.sh",
        in_ts="20161107-141548",
        tsdb_config_dest="/opt/zenoss/etc/opentsdb/opentsdb.conf",
        work_dir="reprocess.out/work",
        err_dir="reprocess.out/err",
        log_dir="reprocess.out/log",
        src_dir="reprocess.in",
        start_time="20161113-162336")
    w.run()
