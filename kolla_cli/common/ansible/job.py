# Copyright(c) 2016, Oracle and/or its affiliates.  All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import fcntl
import json
import logging
import os
import pwd
import re
import subprocess  # nosec
import time

from kolla_cli.common.inventory import remove_temp_inventory
from kolla_cli.common.utils import get_kolla_actions_path
from kolla_cli.common.utils import Lock
from kolla_cli.common.utils import PidManager
from kolla_cli.common.utils import run_cmd
from kolla_cli.common.utils import safe_decode
import kolla_cli.i18n as u

LOG = logging.getLogger(__name__)

LINE_LENGTH = 80

ANSIBLE_1_OR_MORE = 'One or more items failed'


class AnsibleJob(object):
    """class for running ansible commands"""

    def __init__(self, cmd, deploy_id, print_output, inventory_path):
        self._command = cmd
        self._deploy_id = deploy_id
        self._print_output = print_output
        self._temp_inv_path = inventory_path

        self._process = None
        self._process_std_err = None
        self._errors = []
        self._error_total = 0
        self._ignore_total = 0
        self._cmd_output = ''
        self._kill_uname = None
        self._ansible_lock = Lock(owner='ansible_job')
        self._ignore_error_strings = None
        self._host_ignored_error_count = {}

    def run(self):
        try:
            locked = self._ansible_lock.wait_acquire()
            if not locked:
                raise Exception(
                    u._('unable to get lock: {lock}, to run '
                        'ansible job: {cmd} ')
                    .format(lock=self._ansible_lock.lockpath,
                            cmd=self._command))

            LOG.debug('playbook command: %s' % self._command)
            # ansible 2.2 and later introduced an issue where if
            # the playbook is executed from within a directory without
            # read / write permission (which can happen when you,
            # for example, execute via sudo) it will fail. the
            # workaround will be to run the ansible command from /tmp
            # and then change back to the original directory at the end
            current_dir = os.getcwd()  # nosec
            os.chdir('/tmp')  # nosec
            self._process = subprocess.Popen(self._command,  # nosec
                                             shell=True,
                                             stdout=subprocess.PIPE,
                                             stderr=subprocess.PIPE)

            # setup stdout to be read without blocking
            LOG.debug('process pid: %s' % self._process.pid)
            flags = fcntl.fcntl(self._process.stdout, fcntl.F_GETFL)
            fcntl.fcntl(self._process.stdout, fcntl.F_SETFL,
                        (flags | os.O_NONBLOCK))

            # this is also part of the fix for ansible 2.2 and later
            os.chdir(current_dir)
        except Exception as e:
            self._cleanup()
            raise e

    def wait(self):
        """wait for job to complete

        return status of job (see get_status for status values)
        """
        while True:
            status = self.get_status()
            if status is not None:
                break
            time.sleep(0.2)
        return status

    def get_status(self):
        """get process status

        status:
        - None: running
        - 0: done, success
        - 1: done, error
        - 2: done, killed by user
        """
        status = self._process.poll()
        out = self._read_stream(self._process.stdout)
        self._cmd_output = ''.join([self._cmd_output, out])

        # unnecessary spaces should be hidden
        if out:
            self._log_output(out)
        if status is not None:
            # job has completed
            if self._kill_uname:
                status = 2
                msg = (u._('Job killed by user ({name})')
                       .format(name=self._kill_uname))
                self._errors = [msg]
            else:
                status = self._process.returncode
                if status != 0:
                    # if the process ran and returned a non zero return
                    # code we want to see if we got some ansible errors
                    # and if so if we ignored all the errors. if all
                    # errors are ignored we consider the job a success
                    if (self._error_total > 0 and
                            self._error_total == self._ignore_total):
                        status = 0
                    else:
                        status = 1
            if not self._process_std_err:
                # read stderr from process
                std_err = self._read_stream(self._process.stderr)
                self._process_std_err = std_err.strip()
            self._cleanup()
        return status

    def get_error_message(self):
        """"get error message"""
        msg = ''
        for error in self._errors:
            if error:
                msg = ''.join([msg, error, '\n'])

        if ANSIBLE_1_OR_MORE in msg:
            msg = self._get_msg_from_cmdout(msg)
        if not msg:
            msg = self._process_std_err
        return msg

    def get_command_output(self):
        """get command output

        get final output text from command execution
        """
        return self._cmd_output

    def kill(self):
        """kill job in progress

        The process pid is owned by root, so
        that is not killable. Need to kill all its children.
        """
        # the kill must be run as the kolla user so the
        # kolla_actions program must be used.
        try:
            actions_path = get_kolla_actions_path()
            cmd_prefix = ('%s job -t -p '
                          % actions_path)

            # kill the children from largest to smallest pids.
            child_pids = PidManager.get_child_pids(self._process.pid)
            for child_pid in sorted(child_pids, reverse=True):
                cmd = ''.join([cmd_prefix, child_pid])
                err_msg, output = run_cmd(cmd, print_output=False)
                if err_msg:
                    LOG.debug('kill failed: %s %s' % (err_msg, output))
                else:
                    LOG.debug('kill succeeded: %s' % child_pid)

            # record the name of user who killed the job
            cur_uid = os.getuid()
            self._kill_uname = pwd.getpwuid(cur_uid)[0]
        finally:
            self._cleanup()

    def _get_msg_from_cmdout(self, msg):
        """get message from command output

        This is where the error message is in cmd out-
        \nfailed: [ol7-c5] (item=[u'/etc/kolla/config/aodh.conf',
        u'/usr/share/kolla/templates/aodh/aodh.conf_augment']) =>
        {"failed": true, "invocation": {"module_args": {"dest":
        "/usr/share/kolla/templates/aodh/aodh.conf_augment",
        "src": "/etc/kolla/config/aodh.conf"}, "module_name": "template"},
        "item": ["/etc/kolla/config/aodh.conf",
        "/usr/share/kolla/templates/aodh/aodh.conf_augment"],
        "msg": "IOError: [Errno 2] No such file or directory:
        u'/etc/kolla/config/aodh.conf'"}\n
        """
        fail_key = '\nfailed: '
        hostnames = re.findall(fail_key + r'\[(.+?)]', self._cmd_output)
        msgs = re.findall(fail_key + '.+ => (.+?)\n', self._cmd_output)

        for i in range(0, min(len(hostnames), len(msgs))):
            err = ''
            hostname = hostnames[i]
            ans_dict_str = msgs[i]
            try:
                ans_dict = json.loads(ans_dict_str)
                err = ans_dict.get('msg', '')
            except Exception as e:
                LOG.warn('Exception reading cmd_out ansible dictionary: %s'
                         % str(e))
            msg = ''.join([msg, 'Host: ', hostname, ', ', err, '\n'])
        return msg

    def _read_stream(self, stream):
        out = ''
        if stream and not stream.closed:
            try:
                out = safe_decode(stream.read())
            except IOError:  # nosec
                # error can happen if stream is empty
                pass
            if out is None:
                out = ''
        return out

    def _log_lines(self, lines):
        if self._print_output:
            for line in lines:
                LOG.info(line)

    def _log_output(self, output):
        if self._print_output:
            LOG.info(output)

    def _cleanup(self):
        """cleanup job

        - release the ansible lock
        - close stdout and stderr
        - delete temp inventory
        """
        # try to clear the ansible lock
        self._ansible_lock.release()

        # close the process's stdout and stderr streams
        if (self._process and self._process.stdout and not
           self._process.stdout.closed):
            self._process.stdout.close()
        if (self._process and self._process.stderr and not
           self._process.stderr.closed):
            self._process.stderr.close()

        # delete temp inventory file
        remove_temp_inventory(self._temp_inv_path)
