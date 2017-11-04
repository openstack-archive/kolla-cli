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
import tempfile
import time

import kollacli.i18n as u

from kollacli.common.inventory import remove_temp_inventory
from kollacli.common.utils import get_admin_uids
from kollacli.common.utils import get_admin_user
from kollacli.common.utils import get_ansible_lock_path
from kollacli.common.utils import get_kolla_actions_path
from kollacli.common.utils import Lock
from kollacli.common.utils import PidManager
from kollacli.common.utils import run_cmd
from kollacli.common.utils import safe_decode

LOG = logging.getLogger(__name__)

LINE_LENGTH = 80

PIPE_NAME = '.kolla_pipe'

# action defs
ACTION_PLAY_START = 'play_start'
ACTION_TASK_START = 'task_start'
ACTION_TASK_END = 'task_end'
ACTION_INCLUDE_FILE = 'includefile'
ACTION_STATS = 'stats'

ANSIBLE_1_OR_MORE = 'One or more items failed'


class AnsibleJob(object):
    """class for running ansible commands"""

    def __init__(self, cmd, deploy_id, print_output, inventory_path):
        self._command = cmd
        self._deploy_id = deploy_id
        self._print_output = print_output
        self._temp_inv_path = inventory_path

        self._fragment = ''
        self._is_first_packet = True
        self._fifo_path = os.path.join(
            tempfile.gettempdir(),
            'kolla_%s' % deploy_id,
            '%s' % PIPE_NAME)
        self._fifo_fd = None
        self._process = None
        self._process_std_err = None
        self._errors = []
        self._error_total = 0
        self._ignore_total = 0
        self._cmd_output = ''
        self._kill_uname = None
        self._ansible_lock = Lock(get_ansible_lock_path(), 'ansible_job')
        self._ignore_error_strings = None
        self._host_ignored_error_count = {}

    def run(self):
        try:
            locked = self._ansible_lock.wait_acquire()
            if not locked:
                raise Exception(
                    u._('unable to get lock: {lock}, to run '
                        'ansible job: {cmd} ')
                    .format(lock=get_ansible_lock_path(), cmd=self._command))

            LOG.debug('playbook command: %s' % self._command)
            # ansible 2.2 and later introduced an issue where if
            # the playbook is executed from within a directory without
            # read / write permission (which can happen when you,
            # for example, execute via sudo) it will fail.  the
            # workaround will be to run the ansible command from /tmp
            # and then change back to the original directory at the end
            current_dir = os.getcwd()  # nosec
            os.chdir('/tmp')  # nosec
            # create and open named pipe, must be owned by kolla group
            os.mkfifo(self._fifo_path)
            _, grp_id = get_admin_uids()
            os.chown(self._fifo_path, os.getuid(), grp_id)
            os.chmod(self._fifo_path, 0o660)
            self._fifo_fd = os.open(self._fifo_path,
                                    os.O_RDONLY | os.O_NONBLOCK)

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
        self._read_from_callback()
        out = self._read_stream(self._process.stdout)
        self._cmd_output = ''.join([self._cmd_output, out])
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
                    # and if so if we ignored all the errors.  if all
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

        # if no error from the callback, check the process error
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
            kolla_user = get_admin_user()
            cmd_prefix = ('/usr/bin/sudo -u %s %s job -t -p '
                          % (kolla_user, actions_path))

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

        Not very pretty, but the only way to get the error detail out of
        ansible when the callback gives you 'One or more items failed'.

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
        hostnames = re.findall(fail_key + '\[(.+?)]', self._cmd_output)
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

    def _cleanup(self):
        """cleanup job

        - delete temp inventory
        - close stdout and stderr
        - close and delete named pipe (fifo)
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

        # close and delete the named pipe (fifo)
        if self._fifo_fd:
            try:
                os.close(self._fifo_fd)
            except OSError:  # nosec
                # fifo already closed
                pass
        if self._fifo_path and os.path.exists(self._fifo_path):
            os.remove(self._fifo_path)

        # delete temp inventory file
        remove_temp_inventory(self._temp_inv_path)

    def _read_from_callback(self):
        """read lines from callback in real-time"""
        data = None
        try:
            data = os.read(self._fifo_fd, 10000000)
            data = safe_decode(data)
        except OSError:  # nosec
            # error can happen if fifo is empty
            pass
        if data:
            LOG.debug('callback packets: %s' % data)
            packets = self._deserialize_packets(data)
            for packet in packets:
                formatted_data = self._format_packet(packet)
                lines = formatted_data.split('\n')
                self._log_lines(lines)

    def _format_packet(self, packet):
        action = packet['action']
        if action == ACTION_INCLUDE_FILE:
            return self._format_include_file(packet)
        elif action == ACTION_PLAY_START:
            return self._format_play_start(packet)
        elif action == ACTION_STATS:
            return self._format_stats(packet)
        elif action == ACTION_TASK_END:
            return self._format_task_end(packet)
        elif action == ACTION_TASK_START:
            return self._format_task_start(packet)
        else:
            raise Exception(u._('Invalid action [{action}] from callback')
                            .format(action=action))

    def _format_include_file(self, packet):
        return 'included: %s' % packet['filename']

    def _format_play_start(self, packet):
        msg = '\n' + self._add_filler('PLAY ', LINE_LENGTH, '*')
        if self._is_first_packet:
            msg += '\nPlaybook: %s' % packet['playbook']
            self._is_first_packet = False
        return msg

    def _format_stats(self, packet):
        # each element is a dictionary with host as key
        msg = '\n' + self._add_filler('PLAY RECAP ', LINE_LENGTH, '*')
        processed = packet['processed']
        ok = packet['ok']
        changed = packet['changed']
        unreachable = packet['unreachable']
        failures = packet['failures']
        for host in processed:
            hostline = '\n%s' % self._add_filler(host, 28, ' ')
            hostline += (': ok=%s'
                         % self._add_filler('%s' % ok[host], 5, ' '))
            hostline += ('changed=%s'
                         % self._add_filler('%s' % changed[host], 5, ' '))
            hostline += ('unreachable=%s'
                         % self._add_filler('%s' % unreachable[host], 5, ' '))
            failure_count = failures[host]
            ignores = self._host_ignored_error_count.get(host, 0)

            # track the total numbers of failures and ignored failures to help
            # determine job success
            self._error_total += failure_count
            self._ignore_total += ignores
            failure_count -= ignores
            hostline += ('failed=%s' %
                         self._add_filler('%s' % failure_count, 5, ' '))
            hostline += 'ignored=%s' % ignores
            msg += hostline
        return msg

    def _format_task_end(self, packet):
        host = packet['host']
        status = packet['status']
        msg = '%s: [%s]' % (status, host)
        if status == 'failed' or status == 'unreachable':
            results_dict = packet['results']
            taskname = packet['task']['name']

            # update saved error messages.  if the error message should be
            # hidden then do not add it to _errors and add to the ignored
            # error count for the host
            formatted_error = self._format_error(taskname, host,
                                                 status, results_dict)
            if self._hide_ignored_errors(formatted_error):
                LOG.debug('Ignored Error: ' + formatted_error)
                self._host_ignored_error_count[host] = \
                    self._host_ignored_error_count.get(host, 0) + 1
            else:
                self._errors.append(formatted_error)
                # format log message
                results = json.dumps(results_dict)
                msg = 'fatal: [%s]: %s! => %s' % \
                      (host, status.upper(), results)
        return msg

    def _format_task_start(self, packet):
        taskname = packet['name']
        task_line = 'TASK [%s] ' % taskname
        msg = '\n' + self._add_filler(task_line, LINE_LENGTH, '*')
        return msg

    def _format_error(self, taskname, host, status, results):
        # get the primary error message
        err_msg = self._safe_get(results, 'msg')

        # there may be more detailed error msgs under results
        sub_results = self._safe_get(results, 'results')
        if sub_results:
            sub_errs = ''
            comma = ''
            for invocation in sub_results:
                is_failed = invocation.get('failed', False)
                if is_failed is True:
                    sub_msg = self._safe_get(invocation, 'msg')
                    if not sub_msg:
                        sub_msg = self._safe_get(invocation, 'stderr')
                        if not sub_msg:
                            self._safe_get(invocation, 'stdout')
                    sub_errs = ''.join([sub_errs, comma, sub_msg])
                    if sub_msg:
                        comma = ', '
            if sub_errs:
                err_msg = ''.join([err_msg, ' [', sub_errs, ']'])

        if not err_msg or not err_msg.strip():
            # sometimes the error message is in std_out
            # eg- "stdout": 'localhost | FAILED! => {"changed": false,
            # "failed": true, "msg": "...msg..."}'
            stdout = self._safe_get(results, 'stdout')
            if '"msg": "' in stdout:
                err_msg = stdout.split('"msg": "')[1]
                err_msg = err_msg.split('"')[0]
            if not err_msg:
                err_msg = stdout

            if not err_msg or not err_msg.strip():
                # if still no err_msg, provide entire result
                try:
                    err_msg = json.dumps(results)
                except Exception as e:
                    LOG.debug('unable to convert results to string' % str(e))
        msg = ('Host: %s, Task: %s, Status: %s, Message: %s' %
               (host, taskname, status, err_msg))
        return msg

    def _safe_get(self, dictionary, key):
        """get value, never return None"""
        val = dictionary.get(key, '')
        if val is None:
            val = ''
        return val

    def _add_filler(self, msg, length, filler):
        num_stars = max(length - len(msg), 0)
        stars = num_stars * filler
        return msg + stars

    def _deserialize_packets(self, data):
        """get json packets from callback

        Packets are delimited by \n's. It's possible that a packet
        is cut in the middle, creating 2 fragments. Need to handle that.

        return list of dictionaries
        """
        packets = []
        has_fragment = True
        if data.endswith('\n'):
            has_fragment = False
        else:
            LOG.debug('fragment found: %s' % data)
        i = 0
        lines = data.split('\n')
        num_lines = len(lines)
        for line in lines:
            i += 1
            if i == 1:
                # first line
                line = self._fragment + line
                self._fragment = ''
            if i == num_lines and has_fragment:
                # last line is incomplete, save as fragment
                self._fragment = line
                break
            if not line:
                # ignore empty string lines
                continue
            info = self.json_load(line)
            if info:
                packets.append(info)
        return packets

    def json_load(self, string_var, raise_on_err=False):
        retval = None
        try:
            retval = json.loads(string_var)
        except Exception as e:
            LOG.error('invalid string for json encoding: %s' % string_var)
            if raise_on_err:
                raise e
        return retval

    def _hide_ignored_errors(self, error_string):
        if self._ignore_error_strings is not None:
            for ignore_string in self._ignore_error_strings:
                pattern = re.compile(ignore_string)
                match = pattern.findall(error_string)
                if match:
                    return True

        return False
