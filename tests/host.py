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
import unittest


class TestFunctional(KollaCliTest):

    def test_host_add_remove(self):
        hosts = self.TestHosts()

        msg = self.run_client_cmd('host list')
        self._check_cli_output(hosts, msg)

        hostname = 'host_test1'
        ip_addr = '1.1.1.1'
        hosts.add(hostname, ip_addr)
        self.run_client_cmd('host add %s %s' % (hostname, ip_addr))

        msg = self.run_client_cmd('host list')
        self._check_cli_output(hosts, msg)

        hostname = 'host_test2'
        ip_addr = '2.2.2.2'
        hosts.add(hostname, ip_addr)
        self.run_client_cmd('host add %s %s' % (hostname, ip_addr))

        msg = self.run_client_cmd('host list')
        self._check_cli_output(hosts, msg)

        hostname = 'host_test2'
        hosts.remove(hostname)
        self.run_client_cmd('host remove %s' % hostname)

        msg = self.run_client_cmd('host list')
        self._check_cli_output(hosts, msg)

        hostname = 'host_test1'
        hosts.remove(hostname)
        self.run_client_cmd('host remove %s' % hostname)

        msg = self.run_client_cmd('host list')
        self._check_cli_output(hosts, msg)

    def test_host_setzone(self):
        hosts = self.TestHosts()
        hostname = 'host_test1'
        ip_addr = '1.1.1.1'
        zonename = 'test_zone1'
        hosts.add(hostname, ip_addr, zonename)
        self.run_client_cmd('zone add %s' % zonename)

        self.run_client_cmd('host add %s %s' % (hostname, ip_addr))
        self.run_client_cmd('host setzone %s %s' % (hostname, zonename))
        msg = self.run_client_cmd('host list')
        self._check_cli_output(hosts, msg)

        zonename = 'test_zone2'
        hosts.add(hostname, ip_addr, zonename)
        self.run_client_cmd('zone add %s' % zonename)

        self.run_client_cmd('host setzone %s %s' % (hostname, zonename))
        msg = self.run_client_cmd('host list')
        self._check_cli_output(hosts, msg)

        zonename = ''
        hosts.add(hostname, ip_addr, zonename)
        self.run_client_cmd('host clearzone %s' % hostname)
        msg = self.run_client_cmd('host list')
        self._check_cli_output(hosts, msg)

    def test_host_install(self):
        test_hosts = self.get_test_hosts()
        if not test_hosts:
            self.log.info('no test_hosts file found, skipping test')
            return

        hostname = test_hosts.get_hostnames()[0]
        net_addr = test_hosts.get_ip(hostname)
        pwd = test_hosts.get_password(hostname)

        self.run_client_cmd('host add %s %s' % (hostname, net_addr))

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

    def _check_cli_output(self, hosts, cli_output):
        """Verify cli data against model data

        The host list cli output looks like this:

            +-----------+---------+------+
            | Host Name | Address | Zone |
            +-----------+---------+------+
            | foobar    | 2.2.2.2 |      |
            | foo       | 1.1.1.1 |      |
            +-----------+---------+------+
        """
        # check for any host in cli output that shouldn't be there
        cli_lines = cli_output.split('\n')
        exp_hosts = hosts.get_hostnames()
        for cli_line in cli_lines:
            if ('|' not in cli_line or
               cli_line.startswith('+') or
               cli_line.startswith('| Host Name ')):
                continue
            cli_host = cli_line.split('|')[1].strip()
            if cli_host:
                self.assertIn(cli_host, exp_hosts,
                              'unexpected host: %s, found in cli output: %s'
                              % (cli_host, cli_lines))

        for hostname in exp_hosts:
            exp_ip = hosts.get_ip(hostname)
            exp_zone = hosts.get_zone(hostname)

            hostname_found = False
            for cli_line in cli_lines:
                if ('|' not in cli_line or
                   cli_line.startswith('+') or
                   cli_line.startswith('| Host Name ')):
                    continue

                tokens = cli_line.split('|')
                if tokens[1].strip() == hostname:
                    hostname_found = True

                    # check network address
                    yaml_ip = tokens[2].strip()
                    self.assertEqual(exp_ip, yaml_ip,
                                     'incorrect ip address in cli output')

                    # check zone
                    yaml_zone = tokens[3].strip()
                    self.assertEqual(exp_zone, yaml_zone,
                                     'incorrect zone in cli output')

            self.assertTrue(hostname_found,
                            'hostname: %s not in cli output: \n%s'
                            % (hostname, cli_output))

if __name__ == '__main__':
    unittest.main()
