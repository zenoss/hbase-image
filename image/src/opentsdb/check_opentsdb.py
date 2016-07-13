#!/usr/bin/env python
"""
check_opentsdb.py [-c check_program] [-p process_name]

Options:

-c -- Specify the name (including path) of a check program. The check
      program should return 0 if the process is healthy. A nonzero
      return will result in the process being restarted

-p -- Specify a process_name.  Restart the supervisor process named
      'process_name' when the check program returns a nonzero status.

-s -- Specify the number of seconds to sleep after restarting the process.
      Defaults to 60.

-f -- Specify the number of consecutive failures before restarting. Checks
      happen at 5 second intervals. Default is 8.

A sample invocation:

check_opentsdb.py -p opentsdb -c ./checkprog.sh -s 45 -f 7
"""

import check_hbase
import getopt
import logging
import os.path
import sys
import subprocess
import xmlrpclib

XMLRPC_URL = 'http://localhost:9001/RPC2'


def usage():

    """Print the usage statement for the program and exit."""

    print __doc__
    sys.exit(255)


def get_headers(line):

    """Given an event header string, split it into a dictionary."""

    headers = dict(x.split(":") for x in line.split())
    return headers


def run_program(args, outfile=None):  # pragma no cover

    """
    Run a program, redirecting stdout to a file.

    Keyword arguments:
    args    -- a list of command-line arguments
    outfile -- filename (full path) for output. If not supplied,
    /tmp/<program name>.out will be used.

    Return:
    Result of program execution
    """

    if outfile is None:
        outfile = ('/tmp/%s.out' % os.path.basename(args[0]))
    with open(outfile, 'a') as out_fh:
        program_result = subprocess.call(args,
                                         stdout=out_fh,
                                         stderr=subprocess.STDOUT)
    return program_result


def write_stdout(outstr):

    """Write a string to the mapped stdout stream."""

    sys.stdout.write(outstr)
    sys.stdout.flush()


def write_stderr(outstr):

    """Write a string to the mapped stderr stream."""

    sys.stderr.write(outstr.strip())
    sys.stderr.write('\n')
    sys.stderr.flush()


def send_ok():

    """Send an OK result to supervisord via stdout."""

    write_stdout('RESULT 2\nOK')


def send_ready():

    """Send a READY result to supervisord via stdout."""

    write_stdout('READY\n')


class CheckOpentsdb(object):

    """
    Class to watch opentsdb, and restart it if needed. It is designed to run in
    a loop and process supervisord events.
    """

    def __init__(self, check_program, watched_program,
                 sleep_interval=600, max_failures=12):
        self.watched_program = watched_program
        self.check_program = check_program
        self.program_state = None
        self.consecutive_fails = 0
        self.max_failures = max_failures
        self.current_wait_seconds = 0
        self.check_interval = 20

        # set up logging
        self.log = logging.getLogger('CheckOpentsdb')
        self.log.setLevel(logging.INFO)
        self.sleep_interval = sleep_interval
        ch_handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - '
                                      '%(name)s.%(funcName)s: %(message)s')
        ch_handler.setFormatter(formatter)
        ch_handler.setLevel(logging.INFO)
        self.log.addHandler(ch_handler)

    def run_check(self):

        """
        Run the check program. Increment or clear the consecutive_fails
        counter according to the result. Return False if the indication is that
        the monitored program needs to be restarted.
        """

        check_output = run_program([self.check_program])
        self.log.debug('Call to %s returned %s',
                       self.check_program,
                       check_output)
        if 0 == check_output:
            self.consecutive_fails = 0
            self.log.debug('Returning True')
            return True
        self.consecutive_fails += 1
        self.log.info('Consecutive_fails incremented to %s',
                      self.consecutive_fails)
        if self.consecutive_fails >= self.max_failures:
            self.log.info('Consecutive fails >= %s. Returning False.',
                          self.max_failures)
            return False
        self.log.info('OpenTsdb health check failed, but consecutive failures '
                      'threshold not exceeded (%s of %s). Returning True.',
                      self.consecutive_fails, self.max_failures)
        return True

    def hbase_is_ready(self):
        """
        Attempt to query HBase for the opentsdb tables. If the tables cannot
        be found in HBase (either because they are not present, or because
        HBase is unreachable), restarting opentsdb will be unhelpful, and
        possibly hurtful.
        """

        chb = check_hbase.CheckHbase()

        if not chb.check_status():
            self.log.info('HBase is not ready. Tables have not been created,'
                          ' or REST server is not answering.')
            return False

        if 0 == chb.get_live_nodes():
            self.log.info('HBase has no region servers active.')
            return False

        self.log.debug('HBase check passed. returning True.')
        return True

    def restart_process(self):  # pragma: no cover

        """Invoke supervisorctl to restart the monitored process."""

        self.log.info('Restarting %s', self.watched_program)
        server = xmlrpclib.Server(XMLRPC_URL)
        server.supervisor.stopProcess(self.watched_program)
        server.supervisor.startProcess(self.watched_program)
        self.consecutive_fails = 0
        self.log.info('Done calling restart. Waiting for %s seconds.',
                      self.sleep_interval)
        self.wait()

    def check_running(self):    # pragma: no cover

        """
        Invoke supervisorctl to determine whether the monitored program is in
        the RUNNING state. Return True if RUNNING, False otherwise.
        """

        self.log.debug('Function entry.')
        result = False
        server = xmlrpclib.Server(XMLRPC_URL)
        info = server.supervisor.getProcessInfo(self.watched_program)
        state = info['statename']
        if state == 'RUNNING':
            self.log.debug('Setting result to True')
            result = True

        self.log.info('Returning %s', result)
        return result

    def get_payload(self, headers):

        """Extract the event payload given the event header line."""

        payload = None
        try:
            payload_line = sys.stdin.read(int(headers['len']))
            payload = dict([x.split(':') for x in payload_line.split()])
        except KeyError:
            self.log.error('Headers does not contain an entry for len.')
            raise
        except ValueError:
            self.log.error('Bad value for length')
            raise
        return payload

    def wait(self, interval=None):
        """Ignore events for a period of time."""
        if interval is None:
            interval = self.sleep_interval
        self.current_wait_seconds = max(self.current_wait_seconds, interval)
        self.log.info('Waiting period set to %s seconds.',
                      self.current_wait_seconds)

    def read_event(self):

        """
        Read an event from stdin. Extract and return the headers and payload.
        """

        self.log.debug('Waiting for input...')
        line = sys.stdin.readline()
        self.log.debug('Line read: %s', line)
        headers = get_headers(line)
        self.log.debug('Headers = %s', headers)
        payload = self.get_payload(headers)
        self.log.debug('Payload = %s', payload)
        return (headers, payload)

    def process_event(self, headers, payload):

        """
        Process an event from supervisord. Determine the type and send it to
        the appropriate handler.
        """

        eventname = None
        self.log.debug('self.program_state = %s', self.program_state)
        try:
            eventname = headers['eventname']
        except KeyError:
            self.log.error('Header did not contain eventname entry')
            raise
        if eventname.startswith('TICK'):
            self.handle_tick_event(headers, payload)
        elif eventname.startswith('PROCESS_STATE'):
            self.handle_process_state_event(headers, payload)
        else:
            send_ok()

    def handle_tick_event(self, headers, payload):

        """Handle TICK events"""

        # Decrement 'sleep' counter
        self.current_wait_seconds = max(self.current_wait_seconds - 5, 0)

        # Check 'sleep' counter - if > 0, return (no processing)
        if self.current_wait_seconds > 0:
            self.log.debug('current_wait_seconds = %s. ignoring events.',
                           self.current_wait_seconds)
            return True
        else:
            self.wait(self.check_interval)

        self.log.debug('(headers=%s,payload=%s)', str(headers), str(payload))
        if self.program_state is None:
            self.log.debug('State is None. Checking whether running.')
            if self.check_running():
                self.log.debug(
                    'Setting program state to PROCESS_STATE_RUNNING'
                )
                self.program_state = 'PROCESS_STATE_RUNNING'
        if self.program_state == 'PROCESS_STATE_RUNNING':
            self.log.debug('Process is running, doing health check')
            if not self.hbase_is_ready():
                self.log.warn('HBase is not running. Until HBase is '
                              'responding, OpenTSDB will not work.')
            elif not self.run_check():
                self.log.warn('Opentsdb health check returned False. '
                              'Attempting to restart_process.')
                self.restart_process()
                self.log.info('Back from restart_process().')
            else:
                self.log.info('Health check returned True.')
        else:
            self.log.info('Program state is %s', self.program_state)

        return True

    def handle_process_state_event(self, headers, payload):

        """Handle PROCESS_STATE events."""

        self.log.debug('(headers=%s,payload=%s)', str(headers), str(payload))
        processname = None
        try:
            processname = payload['processname']
        except KeyError:
            self.log.error('processname not found in payload.')
            raise

        if processname == self.watched_program:
            eventname = None
            try:
                eventname = headers['eventname']
            except KeyError:
                self.log.error('eventname not in headers.')
                raise

            self.log.info('Setting program_state to %s', eventname)
            self.program_state = eventname

        return True

    def runforever(self):

        """Function to loop forever (or until killed), processing events."""

        self.log.info('Starting runforever')
        while 1:
            send_ready()
            self.log.debug('Reading event')
            (headers, payload) = self.read_event()
            self.process_event(headers, payload)
            send_ok()


def check_opentsdb_from_args(arguments):

    """
    Given command-line program arguments, create an instance of CheckOpentsdb
    to process supervisord events.
    """

    short_args = "hp:c:s:f:"
    long_args = [
        "help",
        "program=",
        "check_program=",
        "sleep_interval=",
        "max_failures=",
    ]

    if not arguments:
        return None
    try:
        opts, _ = getopt.getopt(arguments, short_args, long_args)
    except getopt.GetoptError:
        return None

    check_program = None
    watched_program = None
    sleep_interval = 60
    max_failures = 8

    for option, value in opts:
        if option in ('-h', '--help'):
            return None

        if option in ('-c', '--check_program'):
            check_program = value

        if option in ('-p', '--program'):
            watched_program = value

        if option in ('-s', '--sleep_interval'):
            sleep_interval = int(value)

        if option in ('-f', '--max_failures'):
            max_failures = int(value)

    check_opentsdb = CheckOpentsdb(check_program=check_program,
                                   watched_program=watched_program,
                                   sleep_interval=sleep_interval,
                                   max_failures=max_failures)
    return check_opentsdb


def main():

    """Main function for the program."""

    check_opentsdb = check_opentsdb_from_args(sys.argv[1:])
    if check_opentsdb is None:
        usage()

    # Assume when we start, the system is coming up. Start monitoring with a
    # wait, so opentsdb has time to come up cleanly.
    check_opentsdb.wait()
    check_opentsdb.runforever()

if __name__ == '__main__':
    main()
