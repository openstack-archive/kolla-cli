# Copyright(c) 2016, Oracle and/or its affiliates.  All Rights Reserved.

# TODO(snoyes) - Need to add Oracle GPL3 license here
#
import json
import os
import tempfile
import time
import traceback

from ansible.plugins.callback import CallbackBase

KOLLA_LOG_PATH = '/tmp/ansible'
DEBUG = True

# deploy_id, a unique id for each playbook run
deploy_id = ''

# path to the named pipe fifo
fifo_path = None

# is this a playbook command
is_playbook = False

# playbook path
playbook_path = ''

# flag that play failed waiting for pipe to be opened by client
fifo_failed = False


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
        is_playbook = True
        playbook_path = playbook._file_name
        log('Playbook starting: %s ***************************************'
            % playbook_path)

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
            global fifo_failed

            self.ansible_play = ansible_play

            # for now, ignore ad-hoc ansible commands TODO(snoyes)
            if is_playbook and not fifo_failed:
                # play is the first action of a playbook, set the
                # deploy_id if it doesn't yet exist.
                if not deploy_id:
                    deploy_id = self.get_deploy_id()

                if deploy_id and not fifo_path:
                    self._open_fifo()

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
            out['action'] = 'play_start'
            out['playbook'] = playbook_path
            out['id'] = self.get_id()
            return json.dumps(out)

        def start(self):
            if deploy_id:
                play_ser = self.serialize()
                if DEBUG:
                    log('(%s) play start [%s]'
                        % (deploy_id, play_ser))
                _send_msg(play_ser)

        def _open_fifo(self):
            global fifo_path
            global fifo_failed

            fifo_path = os.path.join(tempfile.gettempdir(),
                                     'kolla_pipe_%s' % deploy_id)

            # Create the pipe, will be owned by kolla:kolla.
            # The client will see this appear and then open the pipe
            # for reading.
            log('creating named pipe: %s' % fifo_path)
            os.mkfifo(fifo_path)

            # wait for pipe to be opened by the client for reading.
            timeout = time.time() + 5
            is_opened_for_read = False
            while time.time() < timeout:
                try:
                    # avoid blocking on open
                    os.open(fifo_path, os.O_WRONLY | os.O_NONBLOCK)
                    is_opened_for_read = True
                    break
                except OSError:
                    time.sleep(1)
            if not is_opened_for_read:
                log('ERROR: timed out waiting for open fifo: %s' % fifo_path)
                fifo_failed = True

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
            task_ser = self.serialize('task_start')
            if DEBUG:
                msg = ('(%s) start task [%s]'
                       % (deploy_id, task_ser))
                log(msg)
            _send_msg(task_ser)

        def end(self, result):
            result_ser = result.serialize()
            if DEBUG:
                msg = ('(%s) end task [%s]'
                       % (deploy_id, result_ser))
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
            out['action'] = 'task_end'
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
            if DEBUG:
                msg = ('(%s) included file: %s'
                       % (deploy_id, include_ser))
                log(msg)
            _send_msg(include_ser)

        def serialize(self):
            out = {}
            out['action'] = 'includefile'
            out['filename'] = self.get_filename()
            out['task'] = self.get_task().convert_to_dictionary()
            return json.dumps(out)

    class AggregateStats(object):
        """AggregateStats class for hiding ansible methods"""
        def __init__(self, ans_stats):
            # each of the stats members is a dictionary
            # with the hostname as the key
            self.anible_stats = ans_stats

        def serialize(self):
            out = {}
            out['action'] = 'stats'
            out['processed'] = self.anible_stats.processed
            out['ok'] = self.anible_stats.ok
            out['dark'] = self.anible_stats.dark
            out['changed'] = self.anible_stats.changed
            out['skipped'] = self.anible_stats.skipped
            return json.dumps(out)

        def start(self):
            stats_ser = self.serialize()
            if DEBUG:
                msg = ('(%s) stats: %s'
                       % (deploy_id, stats_ser))
                log(msg)
            _send_msg(stats_ser)


def _send_msg(msg):
    """send json string msg

    An open and close is done on each message so that the
    pipe reader will see each line as it is written.
    """
    global fifo_path
    global fifo_failed

    if fifo_failed:
        return

    fifo_fd = None
    try:
        fifo_fd = os.open(fifo_path, os.O_WRONLY | os.O_NONBLOCK)
        os.write(fifo_fd, msg)
    except Exception:
        log('ERROR: send_msg: %s' % traceback.format_exc())
    finally:
        if fifo_fd:
            os.close(fifo_fd)


def log(msg):
    if DEBUG:
        with open('%s/kolla.log' % KOLLA_LOG_PATH, 'a') as f:
            f.write('%s: %s\n' % (time.ctime(), msg))
