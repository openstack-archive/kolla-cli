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
import traceback

import testtools

import kollaclient.utils as utils


TEST_SUFFIX = '/test/'
ENV_ETC = 'KOLLA_CLIENT_ETC'
VENV_PY_PATH = '/.venv/bin/python'
KOLLA_CMD = 'kollaclient'


class KollaClientTest(testtools.TestCase):

    cmd_prefix = ''
    log = logging.getLogger(__name__)

    def setUp(self):
        super(KollaClientTest, self).setUp()

        logging.basicConfig(stream=sys.stderr)
        logging.getLogger(__name__).setLevel(logging.DEBUG)

        # switch to test path
        self._setup_env_var()
        etc_path = os.getenv('KOLLA_CLIENT_ETC')
        self.log.debug('$KOLLA_CLIENT_ETC for tests: %s' % etc_path)

        self._set_cmd_prefix()

        # make sure hosts and zones yaml files exist
        # and clear them out
        self._init_dir(etc_path)
        hosts_path = etc_path + '/hosts.yml'
        self._init_file(hosts_path)
        zones_path = etc_path + '/zones.yml'
        self._init_file(zones_path)

    def tearDown(self):
        self._restore_env_var()
        super(KollaClientTest, self).tearDown()

    def run_client_cmd(self, cmd):
        full_cmd = ('%s %s' % (self.cmd_prefix, cmd))
        self.log.debug('running command: %s' % cmd)
        (retval, msg) = self._run_command(full_cmd)

        self.assertEqual(0, retval, ('command failed: (%s), cmd: %s'
                                     % (msg, full_cmd)))
        return msg

    # PRIVATE FUNCTIONS ----------------------------------------------------
    def _setup_env_var(self):
        new_etc_path = utils.get_client_etc() + TEST_SUFFIX
        os.environ[ENV_ETC] = new_etc_path

    def _restore_env_var(self):
        etc_path = utils.get_client_etc()
        if etc_path.endswith(TEST_SUFFIX):
            etc_path = etc_path.rsplit('/', 1)[0]
            os.environ[ENV_ETC] = etc_path

    def _run_command(self, cmd):
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
            retval = e.errno
            msg = 'Unexpected exception: %s' % traceback.format_exc()

        # the py dev debugger adds a string at the line start, remove it
        if msg.startswith('pydev debugger'):
            msg = msg.split('\n', 1)[1]
        return (retval, msg)

    def _init_file(self, filepath):
        with open(filepath, 'w') as f:
            f.close()

    def _init_dir(self, path):
        if not os.path.isdir(path):
            os.makedirs(path)

    def _set_cmd_prefix(self):
        """Select the command to invoke the kollacli

            The kolla-client can be run:

            1) from the command line via $ KOLLA_CMD, or

            2) if that doesn't work, this assumes that we're operating
            in a dev't debug environment, which means that the kollacli
            was installed in a virtualenv. So then we have to use the python
            version in virtualenv and the tests will have to be run
            from the tests directory.
        """
        (_, msg) = self._run_command('which python')
        self.log.debug('starting with python: %s' % msg)
        self.cmd_prefix = KOLLA_CMD
        (retval, msg) = self._run_command('%s host add -h' % self.cmd_prefix)
        if retval == 0:
            self.log.debug('%s found, will use as the test command'
                           % KOLLA_CMD)
            return

        self.log.debug('%s exec failed: %s' % (KOLLA_CMD, msg))
        self.log.debug('look for kollacli shell in virtual env')

        # try to see if this is a debug virtual environment
        # will run the tests via kollacli/shell.sh and
        # use the python in .venv/bin/python
        cwd = os.getcwd()
        if cwd.endswith('tests'):
            os_kolla_dir = cwd.rsplit('/', 1)[0]

            shell_dir = os_kolla_dir + '/%s/' % KOLLA_CMD
            shell_path = shell_dir + 'shell.py'

            python_path = os_kolla_dir + VENV_PY_PATH

            self.log.debug('shell_path: %s' % shell_path)
            self.log.debug('python_path: %s' % python_path)
            if os.path.exists(shell_path) and os.path.exists(python_path):
                self.cmd_prefix = '%s %s ' % (python_path, shell_path)

                self.run_client_cmd('host add -h')
                self.log.info('successfully ran command in venv environment')
                return

        self.assertEqual(0, 1,
                         'no kollacli shell command found. Aborting tests')
