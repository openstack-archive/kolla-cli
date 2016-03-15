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
import subprocess  # nosec
import tempfile
import time

from kollacli.common.utils import get_admin_uids
from kollacli.common.utils import safe_decode

LOG = logging.getLogger(__name__)

LINE_LENGTH = 80

PIPE_PREFIX = '.kolla_pipe_'

# action defs
ACTION_PLAY_START = 'play_start'
ACTION_TASK_START = 'task_start'
ACTION_TASK_END = 'task_end'
ACTION_INCLUDE_FILE = 'includefile'
ACTION_STATS = 'stats'


class AnsibleCommand(object):
    """class for running ansible commands"""

    def __init__(self, command, deploy_id, print_output=True):
        self.command = command
        self.print_output = print_output
        self.deploy_id = deploy_id
        self.fragment = ''
        self.is_first_packet = True
        self.fifo_path = os.path.join(tempfile.gettempdir(),
                                      '%s_%s' % (PIPE_PREFIX, self.deploy_id))

    def run(self):
        fifo_fd = None
        try:
            # create and open named pipe, must be owned by kolla group
            os.mkfifo(self.fifo_path, 0o660)
            _, grp_id = get_admin_uids()
            os.chown(self.fifo_path, os.getuid(), grp_id)
            fifo_fd = os.open(self.fifo_path, os.O_RDONLY | os.O_NONBLOCK)

            process = subprocess.Popen(self.command,  # nosec
                                       shell=True,
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE)

            # setup stdout to be read without blocking
            flags = fcntl.fcntl(process.stdout, fcntl.F_GETFL)
            fcntl.fcntl(process.stdout, fcntl.F_SETFL, (flags | os.O_NONBLOCK))

            out = ''
            while process.poll() is None:
                # process is still running

                # need to drain stdout so buffer doesn't fill up and hang
                # process.
                out = self._get_stdout(out, process)

                # log info from kolla callback
                self._log_callback(fifo_fd)
                time.sleep(1)

            ret_code = process.returncode

            # dump any remaining data in the named pipe
            self._log_callback(fifo_fd)
        finally:
            # close the named pipe
            if fifo_fd:
                os.close(fifo_fd)
            if self.fifo_path and os.path.exists(self.fifo_path):
                os.remove(self.fifo_path)
        return out, ret_code

    def _get_stdout(self, out, process):
        try:
            data = process.stdout.read()
            if data:
                out = ''.join([safe_decode(data)])
        except IOError:  # nosec
            # error can happen if stdout is empty
            pass
        return out

    def _log_callback(self, fifo_fd):
        """log info from callback in real-time to log"""
        data = None
        try:
            data = os.read(fifo_fd, 1000000)
            data = safe_decode(data)
        except OSError:  # nosec
            # error can happen if fifo is empty
            pass
        if data and self.print_output:
            packets = self._deserialize_packets(data)
            for packet in packets:
                line = self._format_packet(packet, self.is_first_packet)
                LOG.info(line)
        return

    def _format_packet(self, packet, first_packet_flag):
        action = packet['action']
        if action == ACTION_INCLUDE_FILE:
            return self._format_include_file(packet)
        elif action == ACTION_PLAY_START:
            return self._format_play_start(packet, first_packet_flag)
        elif action == ACTION_STATS:
            return self._format_stats(packet)
        elif action == ACTION_TASK_END:
            return self._format_task_end(packet)
        elif action == ACTION_TASK_START:
            return self._format_task_start(packet)
        else:
            raise Exception('Invalid action [%s] from callback' % action)

    def _format_include_file(self, packet):
        return 'included: %s' % packet['filename']

    def _format_play_start(self, packet, first_packet_flag):
        msg = '\n' + self._add_filler('PLAY ', LINE_LENGTH, '*')
        if first_packet_flag:
            msg += '\nPlaybook: %s' % packet['playbook']
            self.is_first_packet = False
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
            hostline += 'failed=%s' % failures[host]
            msg += hostline
        return msg

    def _format_task_end(self, packet):
        host = packet['host']
        status = packet['status']
        msg = '%s: [%s]' % (status, host)
        if status == 'failed' or status == 'unreachable':
            results = json.dumps(packet['results'])
            msg = 'fatal: [%s]: %s! => %s' % (host, status.upper(), results)
        return msg

    def _format_task_start(self, packet):
        taskname = packet['name']
        task_line = 'TASK [%s] ' % taskname
        msg = '\n' + self._add_filler(task_line, LINE_LENGTH, '*')
        return msg

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
        i = 0
        lines = data.split('\n')
        num_lines = len(lines)
        for line in lines:
            if not line:
                # ignore empty string lines
                continue
            i += 1
            if i == 1:
                # first line
                line = self.fragment + line
                self.fragment = ''
            elif i == num_lines - 1:
                # last line
                if has_fragment:
                    self.fragment = line
                    continue
            try:
                packets.append(json.loads(line))
            except Exception as e:
                LOG.error('invalid line for json encoding: %s' % line)
                raise e
        return packets
