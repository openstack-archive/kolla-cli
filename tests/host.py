# Copyright(c) 2016, Oracle and/or its affiliates.  All Rights Reserved.
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
from common import KollaCliTest
from common import TestConfig

import json
import os
import time
import unittest
import yaml

from kollacli.api.client import ClientApi
from kollacli.api.exceptions import NotInInventory

TEST_YML_FNAME = 'unittest_hosts_setup.yml'

CLIENT = ClientApi()


class TestFunctional(KollaCliTest):

    def test_host_add_remove(self):
        hosts = TestConfig()

        msg = self.run_cli_cmd('host list -f json')
        self._check_cli_output(hosts, msg)

        host1 = 'host_test1'
        host2 = 'host_test2'

        group1 = 'control'

        hosts.add_host(host1)
        self.run_cli_cmd('host add %s' % host1)
        msg = self.run_cli_cmd('host list -f json')
        self._check_cli_output(hosts, msg)

        hosts.add_host(host2)
        self.run_cli_cmd('host add %s' % host2)
        msg = self.run_cli_cmd('host list -f json')
        self._check_cli_output(hosts, msg)

        hosts.remove_host(host2)
        self.run_cli_cmd('host remove %s' % host2)
        msg = self.run_cli_cmd('host list -f json')
        self._check_cli_output(hosts, msg)

        hosts.remove_host(host1)
        self.run_cli_cmd('host remove %s' % host1)
        msg = self.run_cli_cmd('host list -f json')
        self._check_cli_output(hosts, msg)

        # check remove all
        hosts.add_host(host1)
        self.run_cli_cmd('host add %s' % host1)
        hosts.add_host(host2)
        self.run_cli_cmd('host add %s' % host2)
        msg = self.run_cli_cmd('host list -f json')
        self._check_cli_output(hosts, msg)

        hosts.remove_host(host1)
        hosts.remove_host(host2)
        self.run_cli_cmd('host remove all')
        msg = self.run_cli_cmd('host list -f json')
        self._check_cli_output(hosts, msg)

        # check groups in host list
        hosts.add_host(host1)
        hosts.add_group(host1, group1)
        self.run_cli_cmd('host add %s' % host1)
        self.run_cli_cmd('group addhost %s %s' % (group1, host1))
        msg = self.run_cli_cmd('host list -f json')
        self._check_cli_output(hosts, msg)

        hosts.remove_group(host1, group1)
        self.run_cli_cmd('group removehost %s %s' % (group1, host1))
        msg = self.run_cli_cmd('host list -f json')
        self._check_cli_output(hosts, msg)

    def test_host_setup(self):
        test_config = TestConfig()
        test_config.load()

        if not test_config.get_hostnames():
            self.log.info('no hosts found in test_config.json file, ' +
                          'skipping test')
            return

        hostname = test_config.get_hostnames()[0]

        key_path = '/usr/share/kolla/.ssh/authorized_keys'
        test_config.run_remote_cmd(
            'cat /dev/null > %s' % key_path, hostname)

        pwd = test_config.get_password(hostname)

        self.run_cli_cmd('host add %s' % hostname)

        # check if host is not set-up
        timeout = time.time() + 65
        while time.time() <= timeout:
            self.log.info('waiting 65s for ansible ssh session to timeout')
            time.sleep(10)

        # setup the host
        self.run_cli_cmd('host setup %s --insecure %s'
                         % (hostname, pwd))
        # check that the authorized key file size is not 0
        out1 = test_config.run_remote_cmd('ls -l %s' % key_path, hostname)
        size1 = out1.split('kolla kolla')[1].split()[0]
        self.assertNotEqual(size1, '0',
                            '%s is empty on %s' % (key_path, hostname))

        # run setup again in api, should be a no-op, no new keys should exist
        CLIENT.host_setup({hostname: {'password': pwd}})
        out2 = test_config.run_remote_cmd('ls -l %s' % key_path, hostname)
        size2 = out2.split('kolla kolla')[1].split()[0]
        self.assertEqual(size1, size2, 'host setup added an additional key')

        # run checks, should succeed
        self.run_cli_cmd('host check %s' % hostname)
        self.run_cli_cmd('host check --predeploy %s' % hostname)

    def test_hosts_setup(self):
        """test multi-host setup"""
        test_config = TestConfig()
        test_config.load()

        if not test_config.get_hostnames():
            self.log.info('no hosts found in test_config.json file, ' +
                          'skipping test')
            return

        yml_path = self.get_yml_path()
        hostnames = test_config.get_hostnames()
        for hostname in hostnames:
            self.run_cli_cmd('host add %s' % hostname)

        # test all hosts, success path
        use_uname = False
        yml_dict = {}
        for hostname in hostnames:
            yml_dict[hostname] = {}
            password = test_config.get_password(hostname)
            if use_uname:
                yml_dict[hostname]['uname'] = 'root'
            use_uname = not use_uname
            yml_dict[hostname]['password'] = password
        self.write_yml(yml_dict)
        msg = self.run_cli_cmd('host setup --file %s' % yml_path)
        self.log.info(msg)

        # run check with 'all'
        self.run_cli_cmd('host check all')
        self.run_cli_cmd('host check all --predeploy')

        # failure paths

        # no hostname and no file spec
        msg = self.run_cli_cmd('host setup', True)
        self.assertIn('ERROR', msg,
                      'Setup with no command params did not error')

        # hostname and file spec both present
        msg = self.run_cli_cmd('host setup -f zzzzz hostname', True)
        self.assertIn('ERROR', msg, '2 params did not error')

        # non-existent file
        msg = self.run_cli_cmd('host setup -f !INVALID_FILE_PATH!', True)
        self.assertIn('ERROR', msg, 'Non-existent yml file did not error')

        # empty file
        self.write_yml({})
        msg = self.run_cli_cmd('host setup -f %s' % yml_path, True)
        self.assertIn('ERROR', msg, 'Empty yml file did not error')

        # non-existent host
        self.write_yml({'NOT_HOSTNAME': {'password': '123'}})
        msg = self.run_cli_cmd('host setup -f %s' % yml_path, True)
        self.assertIn('ERROR', msg, 'non-existent host did not error')

        # no password for host
        self.write_yml({hostnames[0]: {'uname': 'name'}})
        msg = self.run_cli_cmd('host setup -f %s' % yml_path, True)
        self.assertIn('ERROR', msg, 'no password for host did not error')

    def test_host_api(self):
        # check some of the api not exercised by the CLI
        host1 = 'host_test1'
        host2 = 'host_test2'
        exp_hosts = sorted([host1, host2])
        CLIENT.host_add(exp_hosts)
        hosts = CLIENT.host_get([host1])
        hostnames = []
        for host in hosts:
            hostnames.append(host.name)
        self.assertIn(host1, hostnames, 'host %s is missing in %s'
                      % (host1, hostnames))
        self.assertNotIn(host2, hostnames, 'host %s is unexpectedly in %s'
                         % (host2, hostnames))
        hosts = CLIENT.host_get(exp_hosts)
        hostnames = []
        for host in hosts:
            hostnames.append(host.name)
        self.assertEqual(exp_hosts, sorted(hostnames), 'hosts mismatch')

        CLIENT.host_remove(exp_hosts)
        try:
            CLIENT.host_get(exp_hosts)
            self.assertTrue(False, 'Failed to raise NotInInventory exception')
        except NotInInventory:
            pass
        except Exception as e:
            raise e

        # check the type checking logic
        self.check_types(CLIENT.host_add, [list])
        self.check_types(CLIENT.host_remove, [list])
        self.check_types(CLIENT.host_setup, [dict])
        self.check_types(CLIENT.host_ssh_check, [list])
        self.check_types(CLIENT.async_host_destroy, [list, str, int, bool])
        self.check_types(CLIENT.async_host_precheck, [list, int])

    def test_host_list_nonascii(self):
        hostname = 'host_test1'
        CLIENT.host_add([hostname])

        # this is a groupname in cyrillic chars
        groupname1 = u'\u0414\u0435\u043a\u0430\u0442'
        groupname2 = 'test_group2'  # ascii groupname
        groupnames = [groupname1, groupname2]
        CLIENT.group_add(groupnames)
        groups = CLIENT.group_get(groupnames)
        for group in groups:
            group.add_host(hostname)

        msg = self.run_cli_cmd('host list')
        self.assertIn(groupname1, msg)
        self.assertNotIn("u'\u0414\u0435\u043a\u0430\u0442'", msg, 'groupname '
                         'incorrectly appearing as unicode bytes in output')
        self.assertNotIn("u'test_group2'", msg, 'unicode escape text is '
                         'incorrectly displayed in host list output')

    def _check_cli_output(self, exp_hosts, cli_output):
        """Verify cli data against model data

        The host list cli output looks like this:

            $ host list -f json
            [{"Host": "foo", "Groups": ["control", "network"]}]
        """
        # check for any host in cli output that shouldn't be there
        cli_hosts = json.loads(cli_output)

        exp_hostnames = exp_hosts.get_hostnames()
        if not exp_hostnames:
            if len(cli_hosts) == 1:
                cli_hostname = cli_hosts[0]['Host']
                if not cli_hostname:
                    # both cli and expected hosts are None
                    return

        for cli_host in cli_hosts:
            cli_hostname = cli_host['Host']
            self.assertIn(cli_hostname, exp_hostnames,
                          'unexpected host: %s, found in cli output: %s'
                          % (cli_hostname, cli_output))

        # check that all expected hosts are in the output
        for exp_hostname in exp_hosts.get_hostnames():
            exp_host_found = False
            for cli_host in cli_hosts:
                if exp_hostname == cli_host['Host']:
                    exp_host_found = True
                    cli_groups = cli_host['Groups']
                    exp_groups = exp_hosts.get_groups(exp_hostname)
                    self.assertEqual(exp_groups, cli_groups)

            self.assertTrue(exp_host_found,
                            'hostname: %s not in cli output: \n%s'
                            % (exp_hostname, cli_output))

    def write_yml(self, yml_dict):
        yml = yaml.dump(yml_dict)
        with open(self.get_yml_path(), 'w') as yml_file:
            yml_file.write(yml)

    def get_yml_path(self):
        home = os.path.expanduser('~')
        return os.path.join(home, TEST_YML_FNAME)

if __name__ == '__main__':
    unittest.main()
