#!/usr/bin/env python

##############################################################################
#
# Copyright (C) Zenoss, Inc. 2016, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
#
##############################################################################
import logging
import os
import shutil
import subprocess
import util


class TSDBWorker(object):
    def __init__(self, metric_name=None, tsdbbin=None, tsdbconfig_src=None,
                 tsdbconfig_dest=None, work_dir=".", err_dir=None,
                 log_dir=None, starttime=None):
        self.metric_name = metric_name
        self.tsdbbin = tsdbbin
        self.tsdbconfig_src = tsdbconfig_src
        self.tsdbconfig_dest = tsdbconfig_dest
        self.work_dir = work_dir
        self.err_dir = err_dir
        self.log_dir = log_dir
        self.startttime = starttime

    @property
    def logger(self):
        return logging.getLogger('migrate.TSDBWorker')

    def get_outfilename(self, operation):
        return "{}-{}-{}.out".format(util.filename_safe(self.metric_name),
                                     self.startttime, operation)


    def get_errfilename(self, operation):
        return "{}-{}-{}.err".format(util.filename_safe(self.metric_name),
                                  self.startttime, operation)

    def get_outfilefullname(self, operation):
        return os.path.join(self.work_dir, self.get_outfilename(operation))


    def get_errfilefullname(self, operation):
        return os.path.join(self.work_dir, self.get_errfilename(operation))

    def export_metric(self):
        cmd = [self.tsdbbin, 'scan', '--config', self.tsdbconfig_src,
               '--import', '0', 'sum', self.metric_name]
        outfile = self.get_outfilefullname('export')
        errfile = self.get_errfilefullname('export')
        status= self.run_command(cmd, 'export')
        self.logger.debug("run_command(%s) returned status: %s, outfile: %s, "
                          "errfile: %s", cmd, status, outfile, errfile)
        if status:
            #TODO: check errfile (and stdout?) for ERROR
            self.logger.debug("removing %s", errfile)
            os.remove(errfile)
        else:
            shutil.move(errfile, self.err_dir)
            shutil.move(outfile, self.err_dir)
        return status

    def import_metric(self):
        datafile = os.path.join(self.work_dir, self.get_outfilename('export'))
        cmd = [self.tsdbbin, "import", "--config", self.tsdbconfig_dest,
               datafile]
        errfile = self.get_errfilefullname("import")
        outfile = self.get_outfilefullname("import")
        status = self.run_command(cmd, "import")

        if status:
            #TODO: check errfile (and stdout?) for ERROR
            self.logger.debug("removing %s", errfile)
            os.remove(errfile)
            self.logger.debug("removing %s", outfile)
            os.remove(outfile)
            self.logger.debug("removing %s", datafile)
            os.remove(datafile)
        else:
            # no success, move out/err files to error directory
            self.logger.debug("moving %s to %s", errfile, self.err_dir)
            shutil.move(errfile, self.err_dir)
            self.logger.debug("moving %s to %s", outfile, self.err_dir)
            shutil.move(outfile, self.err_dir)
            self.logger.debug("moving %s to %s", datafile, self.err_dir)
            shutil.move(datafile, self.err_dir)
        return status

    # def run_command(self, cmd, fn_base):
    def run_command(self, cmd, operation):
        stdoutfile = self.get_outfilefullname(operation)
        stderrfile = self.get_errfilefullname(operation)
        with open(stdoutfile, 'awt') as out_f, \
                open(stderrfile, 'awt') as err_f:
            proc = subprocess.Popen(cmd, stdout=out_f, stderr=err_f)
            proc.wait()
            return proc.returncode == 0

    def migrate_data(self):
        self.logger.info("exporting metric %s", self.metric_name)
        if self.export_metric():
            self.logger.info("importing metric %s", self.metric_name)
            status =  self.import_metric()
            if status:
                pass
                # # all was good, so we can remove the datafile
                # datafile = self.get_outfilefullname('export')
                #
                # self.logger.debug("removing %s", datafile)
                # os.remove(datafile)
        else:
            self.logger.info("error exporting metric %s", self.metric_name)
            return False
        return status

    def run(self):
        self.logger.debug("run() for worker with metric %s", self.metric_name)
        result = False
        try:
            result = self.migrate_data()
        except Exception as e:
            self.logger.exception("exception raised in migrate_data: %s", e)
        return result
