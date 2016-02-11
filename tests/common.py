# Copyright(c) 2015, Oracle and/or its affiliates.  All Rights Reserved.
#
#   Licensed under the Apache License, Version 2.0 (the "License"); you may
#   not use this file except in compliance with the License. You may obtain
#   a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#   WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#   License for the specific language governing permissions and limitations
#   under the License.
#
import logging
import os
import subprocess
import sys
import testtools
import traceback
import yaml

import kollacli.common.utils as utils

from pexpect import pxssh

TEST_SUFFIX = 'test/'
VENV_PY_PATH = '.venv/bin/python'
KOLLA_CMD = 'kollacli'
KOLLA_SHELL_DIR = 'kollacli'

CFG_FNAME = 'test_config.yml'


class KollaCliTest(testtools.TestCase):

    saved_kolla_etc = ''
    cmd_prefix = ''
    log = logging.getLogger(__name__)

    def setUp(self):
        super(KollaCliTest, self).setUp()

        logging.basicConfig(stream=sys.stderr)
        self.log.setLevel(logging.DEBUG)
        self.log.info('\nStarting test: %s ***********************************'
                      % self._testMethodName)

        # switch to test path
        self.log.info('running python: %s/%s' % (sys.executable, sys.version))
        etc_path = utils.get_kollacli_etc()
        self.log.debug('etc for tests: %s' % etc_path)

        self._set_cmd_prefix()

        # make sure inventory dirs exists and remove inventory file
        self._init_dir(etc_path)
        etc_ansible_path = os.path.join(etc_path, 'ansible/')
        self._init_dir(etc_ansible_path)
        self._init_file(os.path.join(etc_ansible_path, 'inventory.json'))

    def run_cli_cmd(self, cmd, expect_error=False):
        full_cmd = ('%s %s' % (self.cmd_prefix, cmd))
        self.log.debug('running command: %s' % cmd)
        (retval, msg) = self.run_command(full_cmd)

        if not expect_error:
            self.assertEqual(0, retval, ('command failed: (%s), cmd: %s'
                                         % (msg, full_cmd)))
        return msg

    # PRIVATE FUNCTIONS ----------------------------------------------------
    def run_command(self, cmd):
        """run bash command

        return (retval, msg)
        """
        # self.log.debug('run cmd: %s' % cmd)
        retval = 0
        msg = ''
        try:
            msg = subprocess.check_output(cmd.split(),
                                          stderr=subprocess.STDOUT)

        except subprocess.CalledProcessError as e:
            retval = e.returncode
            msg = e.output

        except Exception as e:
            retval = -1
            msg = ('Unexpected exception: %s, cmd: %s'
                   % (traceback.format_exc(), cmd))

        # the py dev debugger adds a string at the line start, remove it
        msg = utils.safe_decode(msg)
        if msg.startswith('pydev debugger'):
            msg = msg.split('\n', 1)[1]
        return (retval, msg)

    def _init_file(self, filepath):
        with open(filepath, 'w'):
            pass

    def _init_dir(self, path):
        if not os.path.isdir(path):
            os.mkdir(path)

    def _set_cmd_prefix(self):
        """Select the command to invoke the kollacli

            The kolla cli can be run:

            1) from the command line via $ KOLLA_CMD, or

            2) if that doesn't work, this assumes that we're operating
            in a dev't debug environment, which means that the kollacli
            was installed in a virtualenv. So then we have to use the python
            version in virtualenv and the tests will have to be run
            from the tests directory.
        """
        (_, msg) = self.run_command('which python')
        self.log.debug('starting with python: %s' % msg.strip())
        self.cmd_prefix = KOLLA_CMD
        (retval, msg) = self.run_command('%s host add -h' % self.cmd_prefix)
        if retval == 0:
            self.log.debug('%s found, will use as the test command'
                           % KOLLA_CMD)
            return

        # self.log.debug('%s exec failed: %s' % (KOLLA_CMD, msg))
        self.log.debug('look for kollacli shell in virtual env')

        # try to see if this is a debug virtual environment
        # will run the tests via kollacli/shell.sh and
        # use the python in .venv/bin/python
        cwd = os.getcwd()
        if cwd.endswith('tests'):
            os_kolla_dir = cwd.rsplit('/', 1)[0]

            shell_dir = os_kolla_dir + '/%s/' % KOLLA_SHELL_DIR
            shell_path = os.path.join(shell_dir, 'shell.py')

            python_path = os.path.join(os_kolla_dir, VENV_PY_PATH)

            self.log.debug('shell_path: %s' % shell_path)
            self.log.debug('python_path: %s' % python_path)
            if os.path.exists(shell_path) and os.path.exists(python_path):
                self.cmd_prefix = '%s %s ' % (python_path, shell_path)

                self.run_cli_cmd('host add -h')
                self.log.info('successfully ran command in venv environment')
                return

        self.assertEqual(0, 1,
                         'no kollacli shell command found. Aborting tests')


class TestConfig(object):
    """host systems for testing

    This class can either be used for metadata to hold info about test hosts,
    or can be loaded from a test file for info on actual test host machines.
    """
    log = logging.getLogger(__name__)

    def __init__(self):
        self.hosts_info = {}
        self.predeploy_cmds = []

    def remove_host(self, name):
        del self.hosts_info[name]

    def add_host(self, name):
        if name not in self.hosts_info:
            self.hosts_info[name] = {
                'groups': [], 'pwd': '', }

    def get_groups(self, name):
        return self.hosts_info[name]['groups']

    def add_group(self, name, group):
        if group not in self.hosts_info[name]['groups']:
            self.hosts_info[name]['groups'].append(group)

    def remove_group(self, name, group):
        if group in self.hosts_info[name]['groups']:
            self.hosts_info[name]['groups'].remove(group)

    def get_hostnames(self):
        return list(self.hosts_info.keys())

    def set_username(self, name, username):
        self.hosts_info[name]['username'] = username

    def get_username(self, name):
        return self.hosts_info[name]['username']

    def set_password(self, name, password):
        self.hosts_info[name]['pwd'] = password

    def get_password(self, name):
        return self.hosts_info[name]['pwd']

    def get_predeploy_cmds(self):
        return self.predeploy_cmds

    def load(self):
        """load hosts from test_config.json file

        """
        path = self.get_test_config_path()
        with open(path, 'r+') as cfg_file:
            yml_data = cfg_file.read()

        test_cfg = yaml.safe_load(yml_data)

        hosts_info = test_cfg['hosts']
        if hosts_info:
            for hostname, host_info in hosts_info.items():
                uname = host_info['uname']
                pwd = host_info['pwd']
                self.add_host(hostname)
                self.set_password(hostname, pwd)
                self.set_username(hostname, uname)

        self.predeploy_cmds = test_cfg['predeploy_cmds']

    def get_test_config_path(self):
        """get test_config directory"""
        path = ''
        # first check the current directory
        if os.path.exists(CFG_FNAME):
            path = os.path.join(os.getcwd(), CFG_FNAME)
        else:
            # check the user's home directory
            path = os.path.join(os.path.expanduser('~'), CFG_FNAME)
            if not os.path.exists(path):
                raise Exception('%s not found in current ' % CFG_FNAME +
                                'or home directory')
        return path

    def run_remote_cmd(self, cmd, hostname):
        """run remote command on host

        return output from command
        """
        pwd = self.get_password(hostname)
        username = self.get_username(hostname)
        session = pxssh.pxssh()
        session.login(hostname, username, pwd)
        self.log.info('host: %s, run remote cmd: %s' % (hostname, cmd))
        session.sendline(cmd)
        session.prompt()
        out = session.before
        out = utils.safe_decode(out)
        self.log.info(out)
        session.logout()
        return out
