# Copyright(c) 2016, Oracle and/or its affiliates.  All Rights Reserved.

# TODO:snoyes - Need to add Oracle GPL3 license here
#
import json
# import posix_ipc
import time

from ansible.plugins.callback import CallbackBase
# from collections import deque

KOLLA_LOG_PATH = '/tmp/ansible'
DEBUG = True

# deploy_id, a unique id for each playbook run
deploy_id = ''


class CallbackModule(CallbackBase):
    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'notification'
    CALLBACK_NAME = 'kolla_callback'
    CALLBACK_NEEDS_WHITELIST = True

    def __init__(self):
        super(CallbackModule, self).__init__()

        # ipc Message queue
        # self.ipc_queue = None

        # local send queue
        # self.local_sendq = deque(maxlen=1000)

    def v2_playbook_on_include(self, ans_included_file):
        if deploy_id:
            self.IncludedFile(ans_included_file).start()

#     def v2_playbook_on_start(self, playbook):
#         log('Playbook starting: %s' % playbook._file_name)

    def v2_playbook_on_play_start(self, ans_play):
        self.Play(ans_play).start()

    def v2_playbook_on_task_start(self, ans_task, is_conditional):
        if deploy_id:
            self.Task(ans_task).start()

    def v2_runner_on_failed(self, ans_result, ignore_errors=False):
        if deploy_id:
            result = self.Result(ans_result, 'failed')
            result.get_task().end(result)

    def v2_runner_on_ok(self, ans_result):
        if deploy_id:
            result = self.Result(ans_result, 'ok')
            result.get_task().end(result)

    def v2_runner_on_skipped(self, ans_result):
        if deploy_id:
            result = self.Result(ans_result, 'skipped')
            result.get_task().end(result)

    def v2_runner_on_unreachable(self, ans_result):
        if deploy_id:
            result = self.Result(ans_result, 'unreachable')
            result.get_task().end(result)

    class Play(object):
        """Play class for hiding ansible methods"""
        def __init__(self, ansible_play):
            global deploy_id
            self.ansible_play = ansible_play

            # play is the first action of a playbook, set the
            # deploy_id if it doesn't yet exist.
            if not deploy_id:
                deploy_id = self.get_deploy_id()

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
            out = {}
            out['id'] = self.get_id()
            return json.dumps(out)

        def start(self):
            if deploy_id:
                if DEBUG:
                    log('(%s) play start [%s]'
                        % (deploy_id, self.serialize()))

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
            # tasks.add_task(self)
            if DEBUG:
                msg = ('(%s) start task [%s]'
                       % (deploy_id, self.serialize()))
                log(msg)

        def end(self, result):
            if DEBUG:
                msg = ('(%s) end task [%s]'
                       % (deploy_id, result.serialize()))
                log(msg)

        def convert_to_dictionary(self):
            out = {}
            out['name'] = self.get_name()
            out['id'] = self.get_id()
            out['path'] = self.get_path()
            out['role'] = self.get_rolename()
            return out

        def serialize(self):
            return json.dumps(self.convert_to_dictionary())

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
            if DEBUG:
                msg = ('(%s) included file: %s'
                       % (deploy_id, self.serialize()))
                log(msg)

        def serialize(self):
            out = {}
            out['filename'] = self.get_filename()
            out['task'] = self.get_task().convert_to_dictionary()
            return json.dumps(out)

    #     def _send_msg(self, msg):
    #         """send json string msg"""
    #         # push msg onto local send queue
    #         self.local_sendq.appendleft(msg)
    #
    #         if not self.ipc_queue:
    #             pb_path = self.playbook._file_name
    #             self.ipc_queue = posix_ipc.MessageQueue(pb_path,
    #                                                     flags=posix_ipc.O_CREAT)
    #             self.ipc_queue.block = False
    #
    #         # clear out local send queue
    #         msg_count = len(self.local_sendq)
    #         for _ in range(0, msg_count - 1):
    #             # get the oldest msg without removing it from the queue
    #             msg = self.local_sendq[len(self.local_sendq) - 1]
    #             try:
    #                 # send msg
    #                 self.ipc_queue.send(msg)
    #                 # sent OK, remove message from queue
    #                 self.local_sendq.pop()
    #             except:
    #                 # unable to send message, leave it in queue
    #                 return


def log(msg):
    with open('%s/kolla.log' % KOLLA_LOG_PATH, 'a') as f:
        f.write('%s: %s\n' % (time.ctime(), msg))
