##############################################################################
#
# Copyright (C) Zenoss, Inc. 2016, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
#
##############################################################################
import os
import string
import logging


def filename_safe(s):
    valid_chars = "-_.(){}{}".format(string.ascii_letters, string.digits)
    filename = ''.join(c for c in s if c in valid_chars)
    filename = filename.replace(' ', '_')
    return filename


def makefilename(wd, prefix, timestr, suffix, mkdir=True):
    if (mkdir):
        makedirectory(wd)
    safedir = wd
    filename = filename_safe("{}-{}{}".format(prefix, timestr, suffix))
    return os.path.join(safedir, filename)


def handle_pdb(signal, frame):
    """
    handle signals to invoke the Python debugger
    :param _: signal to handle (ignored)
    :param __: stack frame active when signal occurred
    :return: none - invokes debugger
    """
    import pdb
    pdb.set_trace()


def makedirectory(path):
    if not os.path.exists(path):
        os.makedirs(path)


class ProcessFailedError(Exception):
    pass


def run_command(cmd, stdout_handler, errorline_handler):
    no_errors = True
    logging.debug("run_command(%s, %s, %s)", cmd, str(stdout_handler),
                  str(errorline_handler))
    from subprocess import Popen, PIPE
    logging.debug("about to Popen")
    p = Popen(cmd, stdout=PIPE, stderr=PIPE, bufsize=1)
    logging.debug("after Popen:")
    error_lines = []
    for line in iter(p.stdout.readline, ''):
        if stdout_handler(line) is False:
            no_errors = False
            errorline_handler(line)

    p.stdout.close()

    for line in iter(p.stderr.readline, ''):
        errorline_handler(line)

    p.stderr.close()

    if p.wait() != 0:
        logging.warning("Process for command %s failed - exit status %d",
                        cmd, p.returncode)
        raise ProcessFailedError("{} failed, exit status: {}"
                                 .format(cmd, p.returncode))
    return no_errors
