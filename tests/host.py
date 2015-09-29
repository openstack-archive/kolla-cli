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
import time
import unittest


class TestFunctional(KollaCliTest):

    def test_host_add_remove(self):
        hosts = TestHosts()

        msg = self.run_cli_cmd('host list -f json')
        self._check_cli_output(hosts, msg)

        host1 = 'host_test1'
        host2 = 'host_test2'

        group1 = 'control'

        hosts.add(host1)
        self.run_cli_cmd('host add %s' % host1)
        msg = self.run_cli_cmd('host list -f json')
        self._check_cli_output(hosts, msg)

        hosts.add(host2)
        self.run_cli_cmd('host add %s' % host2)
        msg = self.run_cli_cmd('host list -f json')
        self._check_cli_output(hosts, msg)

        hosts.remove(host2)
        self.run_cli_cmd('host remove %s' % host2)
        msg = self.run_cli_cmd('host list -f json')
        self._check_cli_output(hosts, msg)

        hosts.remove(host1)
        self.run_cli_cmd('host remove %s' % host1)
        msg = self.run_cli_cmd('host list -f json')
        self._check_cli_output(hosts, msg)

        # check groups in host list
        hosts.add(host1)
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
        test_hosts = TestHosts()
        test_hosts.load()

        if not test_hosts:
            self.log.info('no test_hosts file found, skipping test')
            return

        hostname = test_hosts.get_hostnames()[0]

        # remove kolla user and certs from host
        test_hosts.run_remote_cmd(
            'yum --assumeyes remove openstack-kolla-preinstall', hostname)

        # ansible may keep the kolla account tied up for up to 60 seconds
        time_out = time.time() + 75
        while time.time() < time_out:
            msg = test_hosts.run_remote_cmd(
                'userdel -r kolla', hostname)
            if 'currently used by process' in msg:
                self.log.info('waiting for kolla acct to free up...')
                time.sleep(10)
            else:
                break

        self.assertNotIn('currently used by process', msg,
                         'kolla user acct not deleted!:  % msg')

        pwd = test_hosts.get_password(hostname)

        self.run_cli_cmd('host add %s' % hostname)

        # check if host is not set-up
        msg = self.run_cli_cmd('host check %s' % hostname, True)
        self.assertIn('ERROR:', msg,
                      'kolla account still exists host after ' +
                      'uninstall: (%s)' % hostname)

        # install the preinstall pkg on the remote host
        test_hosts.run_remote_cmd(
            'yum --assumeyes install openstack-kolla-preinstall', hostname)

        msg = self.run_cli_cmd('host check %s' % hostname, True)
        self.assertIn('ERROR:', msg,
                      'kolla account is accessible prior ' +
                      'to setup: (%s)' % hostname)

        # setup the host
        self.run_cli_cmd('host setup %s --insecure %s'
                         % (hostname, pwd))
        msg = self.run_cli_cmd('host check %s' % hostname, True)
        self.assertNotIn('ERROR:', msg, 'Check after setup failed on ' +
                         'host: (%s)' % hostname)

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


if __name__ == '__main__':
    unittest.main()
