import os
import string

__author__ = 'morr'


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
    # print "run_command({},{})".format(cmd, stdout_handler)
    from subprocess import Popen, PIPE
    # print("about to Popen")
    # p = Popen(cmd, stdout=PIPE, stderr=STDOUT, bufsize=1)
    p = Popen(cmd, stdout=PIPE, stderr = PIPE, bufsize=1)
    # print("after Popen")
    error_lines = []
    for line in iter(p.stdout.readline, ''):
        if stdout_handler(line) is False:
            no_errors = False
            errorline_handler(line)

    p.stdout.close()

    for line in iter(p.stderr.readline,''):
        errorline_handler(line)

    p.stderr.close()

    if p.wait() != 0:
        raise ProcessFailedError("{} failed, exit status: {}"
                                 .format(cmd, p.returncode))
    return no_errors
