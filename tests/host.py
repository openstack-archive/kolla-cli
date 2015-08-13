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
from common import KollaCliTest
from common import TestHosts

import json
import unittest

class TestFunctional(KollaCliTest):

    def test_host_add_remove(self):
        hosts = TestHosts()

        msg = self.run_client_cmd('host list -f json')
        self._check_cli_output(hosts, msg)

        host1 = 'host_test1'
        host2 = 'host_test2'

        group1 = 'control'
        group2 = 'network'
        group3 = 'compute'

        hosts.add(host1)
        hosts.add_group(host1, group1)
        self.run_client_cmd('host add %s %s' % (host1, group1))
        msg = self.run_client_cmd('host list -f json')
        self._check_cli_output(hosts, msg)

        hosts.add_group(host1, group2)
        self.run_client_cmd('host add %s %s' % (host1, group2))
        msg = self.run_client_cmd('host list -f json')
        self._check_cli_output(hosts, msg)

        hosts.remove_group(host1, group1)
        self.run_client_cmd('host remove %s %s' % (host1, group1))
        msg = self.run_client_cmd('host list -f json')
        self._check_cli_output(hosts, msg)

        hosts.add(host2)
        hosts.add_group(host2, group3)
        self.run_client_cmd('host add %s %s' % (host2, group3))
        msg = self.run_client_cmd('host list -f json')
        self._check_cli_output(hosts, msg)

        hosts.remove(host2)
        self.run_client_cmd('host remove %s %s' % (host2, group3))
        msg = self.run_client_cmd('host list -f json')
        self._check_cli_output(hosts, msg)

        hosts.remove(host1)
        self.run_client_cmd('host remove %s' % host1)
        msg = self.run_client_cmd('host list -f json')
        self._check_cli_output(hosts, msg)

#     def test_host_setzone(self):
#         hosts = self.TestHosts()
#         hostname = 'host_test1'
#         ip_addr = '1.1.1.1'
#         zonename = 'test_zone1'
#         hosts.add(hostname, ip_addr, zonename)
#         self.run_client_cmd('zone add %s' % zonename)
#
#         self.run_client_cmd('host add %s %s' % (hostname, ip_addr))
#         self.run_client_cmd('host setzone %s %s' % (hostname, zonename))
#         msg = self.run_client_cmd('host list')
#         self._check_cli_output(hosts, msg)
#
#         zonename = 'test_zone2'
#         hosts.add(hostname, ip_addr, zonename)
#         self.run_client_cmd('zone add %s' % zonename)
#
#         self.run_client_cmd('host setzone %s %s' % (hostname, zonename))
#         msg = self.run_client_cmd('host list')
#         self._check_cli_output(hosts, msg)
#
#         zonename = ''
#         hosts.add(hostname, ip_addr, zonename)
#         self.run_client_cmd('host clearzone %s' % hostname)
#         msg = self.run_client_cmd('host list')
#         self._check_cli_output(hosts, msg)

    def test_host_install(self):
        test_hosts = TestHosts()
        test_hosts.load()

        if not test_hosts:
            self.log.info('no test_hosts file found, skipping test')
            return

        hostname = test_hosts.get_hostnames()[0]
        pwd = test_hosts.get_password(hostname)

        self.run_client_cmd('host add %s control' % (hostname))

        # check if host is installed
        msg = self.run_client_cmd('host check %s' % hostname, True)
        if 'ERROR:' not in msg:
            # host is installed, uninstall it
            self.run_client_cmd('host uninstall %s --insecure %s'
                                % (hostname, pwd))
            msg = self.run_client_cmd('host check %s' % hostname, True)
            self.assertIn('ERROR:', msg, 'Uninstall failed on host: (%s)'
                          % hostname)

        # install the host
        self.run_client_cmd('host install %s --insecure %s'
                            % (hostname, pwd))
        msg = self.run_client_cmd('host check %s' % hostname, True)
        self.assertNotIn('ERROR:', msg, 'Install failed on host: (%s)'
                         % hostname)

        # uninstall the host
        self.run_client_cmd('host uninstall %s --insecure %s'
                            % (hostname, pwd))
        msg = self.run_client_cmd('host check %s' % hostname, True)
        self.assertIn('ERROR:', msg, 'Uninstall failed on host: (%s)'
                      % hostname)

    def _check_cli_output(self, exp_hosts, cli_output):
        """Verify cli data against model data

        The host list cli output looks like this:

            $ host list -f json
            [{"Host Name": "foo", "Groups": ["control", "network"]}]
        """
        # check for any host in cli output that shouldn't be there
        cli_hosts = json.loads(cli_output)

        exp_hostnames = exp_hosts.get_hostnames()
        if not exp_hostnames:
            if len(cli_hosts) == 1:
                cli_hostname = cli_hosts[0]['Host Name']
                if not cli_hostname:
                    # both cli and expected hosts are None
                    return

        for cli_host in cli_hosts:
            cli_hostname = cli_host['Host Name']
            self.assertIn(cli_hostname, exp_hostnames,
                          'unexpected host: %s, found in cli output: %s'
                          % (cli_hostname, cli_output))

        # check that all expected hosts are in the output
        for exp_hostname in exp_hosts.get_hostnames():
            exp_host_found = False
            for cli_host in cli_hosts:
                if exp_hostname == cli_host['Host Name']:
                    exp_host_found = True
                    cli_groups = cli_host['Groups']
                    exp_groups = exp_hosts.get_groups(exp_hostname)
                    self.assertEqual(exp_groups, cli_groups)

            self.assertTrue(exp_host_found,
                            'hostname: %s not in cli output: \n%s'
                            % (exp_hostname, cli_output))


if __name__ == '__main__':
    unittest.main()
