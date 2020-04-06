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
from kolla_cli.tests.functional.common import KollaCliTest

import json
import os
import unittest
import yaml

from kolla_cli.api.client import ClientApi
from kolla_cli.api.exceptions import NotInInventory
from kolla_cli.api.host import Host

TEST_YML_FNAME = 'unittest_hosts_setup.yml'

CLIENT = ClientApi()


class TestFunctional(KollaCliTest):

    def test_host_add_remove(self):
        hosts = {}

        msg = self.run_cli_cmd('host list -f json')
        self._check_cli_output(hosts, msg)

        host1 = 'host_test1'
        host2 = 'host_test2'

        group1 = 'control'

        hosts[host1] = Host(host1)
        self.run_cli_cmd('host add %s' % host1)
        msg = self.run_cli_cmd('host list -f json')
        self._check_cli_output(hosts, msg)

        hosts[host2] = Host(host2)
        self.run_cli_cmd('host add %s' % host2)
        msg = self.run_cli_cmd('host list -f json')
        self._check_cli_output(hosts, msg)

        del hosts[host2]
        self.run_cli_cmd('host remove %s' % host2)
        msg = self.run_cli_cmd('host list -f json')
        self._check_cli_output(hosts, msg)

        del hosts[host1]
        self.run_cli_cmd('host remove %s' % host1)
        msg = self.run_cli_cmd('host list -f json')
        self._check_cli_output(hosts, msg)

        # check remove all
        hosts[host1] = Host(host1)
        self.run_cli_cmd('host add %s' % host1)
        hosts[host2] = Host(host2)
        self.run_cli_cmd('host add %s' % host2)
        msg = self.run_cli_cmd('host list -f json')
        self._check_cli_output(hosts, msg)

        hosts.clear()
        self.run_cli_cmd('host remove all')
        msg = self.run_cli_cmd('host list -f json')
        self._check_cli_output(hosts, msg)

        # check groups in host list
        hosts[host1] = Host(host1, [group1])
        self.run_cli_cmd('host add %s' % host1)
        self.run_cli_cmd('group addhost %s %s' % (group1, host1))
        msg = self.run_cli_cmd('host list -f json')
        self._check_cli_output(hosts, msg)

        # removing group by resetting host1 to new Host with no groups
        hosts[host1] = Host(host1)
        self.run_cli_cmd('group removehost %s %s' % (group1, host1))
        msg = self.run_cli_cmd('host list -f json')
        self._check_cli_output(hosts, msg)

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
        self.check_types(CLIENT.host_destroy, [list, str, int, bool])

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

# TODO(bmace) -- test currently broken
# msg = self.run_cli_cmd('host list')
# self.assertIn(groupname1, msg)
# self.assertNotIn("u'\u0414\u0435\u043a\u0430\u0442'", msg, 'groupname '
#                  'incorrectly appearing as unicode bytes in output')
# self.assertNotIn("u'test_group2'", msg, 'unicode escape text is '
#                  'incorrectly displayed in host list output')

    def _check_cli_output(self, exp_hosts, cli_output):
        """Verify cli data against model data

        The host list cli output looks like this:

            $ host list -f json
            [{"Host": "foo", "Groups": ["control", "network"]}]
        """
        # check for any host in cli output that shouldn't be there
        cli_hosts = json.loads(cli_output)

        if not exp_hosts:
            if len(cli_hosts) == 1:
                cli_hostname = cli_hosts[0]['Host']
                if not cli_hostname:
                    # both cli and expected hosts are None
                    return

        for cli_host in cli_hosts:
            cli_hostname = cli_host['Host']
            self.assertIn(cli_hostname, exp_hosts,
                          'unexpected host: %s, found in cli output: %s'
                          % (cli_hostname, cli_output))

        # check that all expected hosts are in the output
        for exp_host in exp_hosts.values():
            exp_host_found = False
            for cli_host in cli_hosts:
                if exp_host.get_name() == cli_host['Host']:
                    exp_host_found = True
                    cli_groups = cli_host['Groups']
                    exp_groups = exp_host.get_groups()
                    self.assertEqual(exp_groups, cli_groups)

            self.assertTrue(exp_host_found,
                            'hostname: %s not in cli output: \n%s'
                            % (exp_host.get_name(), cli_output))

    def write_yml(self, yml_dict):
        yml = yaml.dump(yml_dict)
        with open(self.get_yml_path(), 'w') as yml_file:
            yml_file.write(yml)

    def get_yml_path(self):
        home = os.path.expanduser('~')
        return os.path.join(home, TEST_YML_FNAME)


if __name__ == '__main__':
    unittest.main()
