# Copyright(c) 2016, Oracle and/or its affiliates.  All Rights Reserved.
#
# This file is part of Oracle OpenStack for Oracle Linux
#
# Oracle OpenStack for Oracle Linux is free software: you can redistribute
# it and/or modify it under the terms of the GNU General Public License as
# published by # the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# Oracle OpenStack for Oracle Linux is distributed in the hope that it will
# be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Oracle OpenStack for Oracle Linux.  If not, see
# <http://www.gnu.org/licenses/>.#
import json
import os
import select
import shutil
import tempfile
import time
import traceback

from ansible.plugins.callback import CallbackBase

PIPE_BUF = select.PIPE_BUF  # depth of fifo buffer

DEBUG_LOG_DIR = '/tmp/ansible_debug'
DEBUG_FLAG_FNAME = '/tmp/ENABLE_ANSIBLE_PLUGIN_DEBUG'
DEBUG_LOG_FNAME = 'plugin.log'

PIPE_NAME = '.kolla_pipe'

TIMEOUT = 5  # 5 second timeout

# action defs
ACTION_PLAY_START = 'play_start'
ACTION_TASK_START = 'task_start'
ACTION_TASK_END = 'task_end'
ACTION_INCLUDE_FILE = 'includefile'
ACTION_STATS = 'stats'

# deploy_id, a unique id for each playbook run
deploy_id = ''

# path to the named pipe fifo
fifo_path = None

# is this a playbook command
is_playbook = False

# playbook path
playbook_path = ''


class CallbackModule(CallbackBase):
    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'notification'
    CALLBACK_NAME = 'kolla_callback'
    CALLBACK_NEEDS_WHITELIST = True

    def __init__(self):
        super(CallbackModule, self).__init__()

    def v2_playbook_on_include(self, ans_included_file):
        if deploy_id:
            try:
                self.IncludedFile(ans_included_file).start()
            except Exception as e:
                log('include err %s %s' % (str(e), traceback.format_exc()))

    def v2_playbook_on_start(self, playbook):
        global is_playbook
        global playbook_path

        log('Playbook starting: ******************************************')
        is_playbook = True
        playbook_path = playbook._file_name
        log('playbook path: %s' % playbook_path)

    def v2_playbook_on_play_start(self, ans_play):
        try:
            self.Play(ans_play).start()
        except Exception:
            log('ERROR: play_start: %s' % traceback.format_exc())

    def v2_playbook_on_task_start(self, ans_task, is_conditional):
        if deploy_id:
            try:
                self.Task(ans_task).start()
            except Exception:
                log('ERROR: task_start: %s' % traceback.format_exc())

    def v2_runner_on_failed(self, ans_result, ignore_errors=False):
        if deploy_id:
            try:
                result = self.Result(ans_result, 'failed')
                result.get_task().end(result)
            except Exception:
                log('ERROR: on_failed: %s' % traceback.format_exc())

    def v2_playbook_on_stats(self, ans_stats):
        if deploy_id:
            try:
                stats = self.AggregateStats(ans_stats)
                stats.start()
            except Exception:
                log('ERROR: on_stats: %s' % traceback.format_exc())

    def v2_runner_on_ok(self, ans_result):
        if deploy_id:
            try:
                result = self.Result(ans_result, 'ok')
                result.get_task().end(result)
            except Exception:
                log('ERROR: on_ok: %s' % traceback.format_exc())

    def v2_runner_on_skipped(self, ans_result):
        if deploy_id:
            try:
                result = self.Result(ans_result, 'skipped')
                result.get_task().end(result)
            except Exception:
                log('ERROR: on_skipped: %s %s' % traceback.format_exc())

    def v2_runner_on_unreachable(self, ans_result):
        if deploy_id:
            try:
                result = self.Result(ans_result, 'unreachable')
                result.get_task().end(result)
            except Exception:
                log('ERROR: on_unreachable: %s %s' % traceback.format_exc())

    class Play(object):
        """Play class for hiding ansible methods

        This is the first call in a playbook run that contains the
        deploy_id.
        """
        def __init__(self, ansible_play):
            global deploy_id
            global fifo_path
            global is_playbook

            self.ansible_play = ansible_play

            # for now, ignore ad-hoc ansible commands TODO(snoyes)
            if is_playbook:
                # play is the first action of a playbook, set the
                # deploy_id if it doesn't yet exist.
                if not deploy_id:
                    deploy_id = self.get_deploy_id()

                if deploy_id:
                    fifo_path = os.path.join(tempfile.gettempdir(),
                                             'kolla_%s' % deploy_id,
                                             '%s' % PIPE_NAME)

        def get_id(self):
            return str(self.ansible_play._uuid)

        def get_deploy_id(self):
            """get deploy id from the inventory directory

            return either deploy_id or '' (empty string)
            """
            tmp_id = ''
            var_mgr = self.ansible_play._variable_manager
            if not var_mgr:
                return tmp_id
            inv = var_mgr._inventory
            if not inv:
                return tmp_id
            inv_dir = inv.basedir()
            if not inv_dir or 'kolla_' not in inv_dir:
                return tmp_id
            tmp_id = inv_dir.split('kolla_')[1]
            return tmp_id

        def serialize(self):
            global playbook_path

            out = {}
            out['action'] = ACTION_PLAY_START
            out['playbook'] = playbook_path
            out['id'] = self.get_id()
            return json.dumps(out)

        def start(self):
            if deploy_id:
                play_ser = self.serialize()
                log('(%s) play start [%s]' % (deploy_id, play_ser))
                _send_msg(play_ser)

    class Task(object):
        """Task class for hiding ansible methods"""
        def __init__(self, ansible_task):
            self.ansible_task = ansible_task

        def get_id(self):
            return str(self.ansible_task._uuid)

        def get_name(self):
            return self.ansible_task.get_name()

        def get_path(self):
            return self.ansible_task.get_path()

        def get_rolename(self):
            rolename = ''
            if self.ansible_task._role:
                rolename = self.ansible_task._role.get_name()
            return rolename

        def start(self):
            task_ser = self.serialize(ACTION_TASK_START)
            msg = ('(%s) start task [%s]' % (deploy_id, task_ser))
            log(msg)
            _send_msg(task_ser)

        def end(self, result):
            result_ser = result.serialize()
            msg = ('(%s) end task [%s]' % (deploy_id, result_ser))
            log(msg)
            _send_msg(result_ser)

        def convert_to_dictionary(self, action=None):
            out = {}
            if action:
                out['action'] = action
            out['name'] = self.get_name()
            out['id'] = self.get_id()
            out['path'] = self.get_path()
            out['role'] = self.get_rolename()
            return out

        def serialize(self, action=None):
            return json.dumps(self.convert_to_dictionary(action))

    class Result(object):
        """Result class for hiding ansible methods"""
        def __init__(self, ansible_result, status):
            self.ansible_result = ansible_result
            self.status = status

        def get_results_dict(self):
            return self.ansible_result._result

        def get_status(self):
            """get status of task

            status values are:
            - 'ok'
            - 'failed'
            - 'skipped'
            - 'unreachable'
            """
            return self.status

        def get_hostname(self):
            return self.ansible_result._host.name

        def get_task(self):
            return CallbackModule.Task(self.ansible_result._task)

        def serialize(self):
            out = {}
            out['action'] = ACTION_TASK_END
            out['host'] = self.get_hostname()
            out['status'] = self.get_status()
            out['results'] = self.get_results_dict()
            out['task'] = self.get_task().convert_to_dictionary()
            return json.dumps(out)

    class IncludedFile(object):
        """IncludedFile class for hiding ansible methods"""
        def __init__(self, ansible_included_file):
            self.ansible_included_file = ansible_included_file

        def get_task(self):
            return CallbackModule.Task(self.ansible_included_file._task)

        def get_filename(self):
            return self.ansible_included_file._filename

        def start(self):
            include_ser = self.serialize()
            msg = ('(%s) included file: %s' % (deploy_id, include_ser))
            log(msg)
            _send_msg(include_ser)

        def serialize(self):
            out = {}
            out['action'] = ACTION_INCLUDE_FILE
            out['filename'] = self.get_filename()
            out['task'] = self.get_task().convert_to_dictionary()
            return json.dumps(out)

    class AggregateStats(object):
        """AggregateStats class for hiding ansible methods"""
        def __init__(self, ans_stats):
            # each of the stats members is a dictionary
            # with the hostname as the key
            self.ansible_stats = ans_stats

        def serialize(self):
            out = {}
            out['action'] = ACTION_STATS
            out['processed'] = self.ansible_stats.processed
            out['failures'] = self.ansible_stats.failures
            out['unreachable'] = self.ansible_stats.dark
            out['changed'] = self.ansible_stats.changed
            out['skipped'] = self.ansible_stats.skipped
            out['ok'] = self.ansible_stats.ok

            # for some odd reason, if any of the stats are 0, the host
            # may (or may not) be ommitted in the dict. fix that up.
            for host in out['processed']:
                self._fix_hosts(host, out['failures'])
                self._fix_hosts(host, out['unreachable'])
                self._fix_hosts(host, out['ok'])
                self._fix_hosts(host, out['changed'])
                self._fix_hosts(host, out['skipped'])

            return json.dumps(out)

        def start(self):
            stats_ser = self.serialize()
            msg = ('(%s) stats: %s' % (deploy_id, stats_ser))
            log(msg)
            _send_msg(stats_ser)

        def _fix_hosts(self, host, stats):
            if host not in stats:
                stats[host] = 0


def _send_msg(msg):
    """send json string msg

    An open and close is done on each message so that the
    pipe reader will see each line as it is written.
    """
    global fifo_path

    fifo_fd = None
    try:
        fifo_fd = os.open(fifo_path, os.O_WRONLY | os.O_NONBLOCK)
        _send_packets(fifo_fd, msg + '\n')
    except Exception:
        log('ERROR: os.open: %s' % traceback.format_exc())
    finally:
        if fifo_fd:
            os.close(fifo_fd)


def _send_packets(fifo_fd, data):
    """make fifo writes atomic

    fifo writes are only atomic up to PIPE_BUF bytes. Keep
    the write to less than that to avoid partial writes.
    """
    start_idx = 0
    while start_idx < len(data):
        end_idx = start_idx + PIPE_BUF - 1
        _fifo_write(fifo_fd, data[start_idx:end_idx])
        start_idx = end_idx


def _fifo_write(fifo_fd, data):
    timeout_target = time.time() + TIMEOUT
    while time.time() < timeout_target:
        try:
            os.write(fifo_fd, data)
            break
        except Exception:
            log('ERROR: send_msg: %s, will retry' % traceback.format_exc())
            time.sleep(1)
    if time.time() > timeout_target:
        log('ERROR: timed out trying to write packet, packet dropped.')


def log(msg):
    if os.path.exists(DEBUG_FLAG_FNAME):
        if not os.path.exists(DEBUG_LOG_DIR):
            os.mkdir(DEBUG_LOG_DIR)
        log_path = os.path.join(DEBUG_LOG_DIR, DEBUG_LOG_FNAME)
        if os.path.exists(log_path):
            size = os.stat(log_path).st_size
            if size > 10000000:
                old_path = '%s.1' % log_path
                shutil.copyfile(log_path, old_path)
                os.remove(log_path)

        with open(log_path, 'a') as f:
            f.write('%s: %s\n' % (time.ctime(), msg))
