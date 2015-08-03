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
import common
import unittest


KEY_NET = 'NetworkAddress'
KEY_SERVICES = 'Services'
KEY_ZONE = 'Zone'


class TestFunctional(common.KollaClientTest):

    def test_host_add_remove(self):
        # host file should be initialized to an empty dict {}
        msg = self.run_client_cmd('host list')
        self.assertEqual('', msg, 'hosts.yml is not empty: %s' % msg)

        hosts = self.Hosts()

        hostname = 'host_test1'
        ip_addr = '1.1.1.1'
        hosts.add(hostname, ip_addr)
        self.run_client_cmd('host add %s %s' % (hostname, ip_addr))

        msg = self.run_client_cmd('host list')
        self._check_hosts_yml(hosts, msg)

        hostname = 'host_test2'
        ip_addr = '2.2.2.2'
        hosts.add(hostname, ip_addr)
        self.run_client_cmd('host add %s %s' % (hostname, ip_addr))

        msg = self.run_client_cmd('host list')
        self._check_hosts_yml(hosts, msg)

        hostname = 'host_test2'
        hosts.remove(hostname)
        self.run_client_cmd('host remove %s' % hostname)

        msg = self.run_client_cmd('host list')
        self._check_hosts_yml(hosts, msg)

        hostname = 'host_test1'
        hosts.remove(hostname)
        self.run_client_cmd('host remove %s' % hostname)

        msg = self.run_client_cmd('host list')
        self._check_hosts_yml(hosts, msg)

    def _check_hosts_yml(self, hosts, hosts_yml):
        """Verify cli data against model data

        The yml is a string representation of a simple yml file,
        that is returned by the host list command; of form:

          \n
          hostname1\n
          {'NetworkAddress': 'ip', 'Services': '[]', 'Zone': 'zone'}\n
          hostname2\n
          {'NetworkAddress': 'ip', 'Services': '[]', 'Zone': 'zone'}\n
          etc
        """
        # check for any host in yml that shouldn't be there
        yml_lines = hosts_yml.split('}\n')
        exp_hosts = hosts.get_hostnames()
        for yml_line in yml_lines:
            yml_line = yml_line.strip()
            if yml_line:
                yml_host = yml_line.split('\n')[0]
                self.assertIn(yml_host, exp_hosts,
                              'yml: %s, contains unexpected host: %s'
                              % (yml_lines, yml_host))

        for hostname in exp_hosts:
            exp_ip = hosts.get_ip(hostname)
            exp_zone = hosts.get_zone(hostname)

            hostname_found = False
            for yml_line in yml_lines:
                yml_line = yml_line.strip()
                if yml_line.startswith(hostname):
                    hostname_found = True

                    # check network info
                    self.assertIn(KEY_NET, yml_line,
                                  'host: %s, has no %s entry in yml'
                                  % (hostname, KEY_NET))
                    ip_start = yml_line.find(KEY_NET) + len(KEY_NET) + 4
                    ip_end = yml_line.find(',', ip_start) - 1
                    ip = yml_line[ip_start: ip_end]
                    self.assertEqual(exp_ip, ip, 'incorrect ip address in yml')

                    # check zone
                    self.assertIn(KEY_NET, yml_line,
                                  'host: %s, has no %s entry in yml'
                                  % (hostname, KEY_ZONE))
                    zn_start = yml_line.find(KEY_ZONE) + len(KEY_ZONE) + 4
                    zn_end = yml_line.find(',', zn_start) - 1
                    zone = yml_line[zn_start: zn_end]
                    self.assertEqual(exp_zone, zone, 'incorrect zone in yml')

                    # check services (TODO(SNOYES))

            self.assertTrue(hostname_found,
                            'hostname: %s not in yml: %s'
                            % (hostname, hosts_yml))

    class Hosts(object):
        """test representation of host data"""
        info = {}

        def remove(self, name):
            del self.info[name]

        def add(self, name, ip, zone='', services=[]):
            if name not in self.info:
                self.info[name] = {}
            self.info[name][KEY_NET] = ip
            self.info[name][KEY_ZONE] = zone
            self.info[name][KEY_SERVICES] = services

        def get_ip(self, name):
            return self.info[name][KEY_NET]

        def get_zone(self, name):
            return self.info[name][KEY_ZONE]

        def get_services(self, name):
            return self.info[name][KEY_SERVICES]

        def get_hostnames(self):
            return self.info.keys()

if __name__ == '__main__':
    unittest.main()
