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
from common import TestConfig

from kollacli.ansible import inventory

import unittest

DISABLED_SERVICES = [
    'cinder', 'glance', 'haproxy', 'heat',
    'horizon', 'keystone', 'murano', 'neutron', 'nova',
    ]
ENABLED_SERVICES = [
    'mysqlcluster', 'rabbitmq',
    ]


class TestFunctional(KollaCliTest):

    def test_destroy(self):
        test_config = TestConfig()
        test_config.load()

        if not test_config:
            self.log.info('no test_config file found, skipping test')
            return

        # add host to inventory
        hostname = test_config.get_hostnames()[0]
        pwd = test_config.get_password(hostname)
        self.run_cli_cmd('host add %s' % hostname)
        self.run_cli_cmd('host setup %s --insecure %s'
                         % (hostname, pwd))

        # add host to all deploy groups
        for group in inventory.DEPLOY_GROUPS:
            self.run_cli_cmd('group addhost %s %s' % (group, hostname))

        # disable most services so the test is quicker
        for disabled_service in DISABLED_SERVICES:
            self.run_cli_cmd('property set enable_%s no' % disabled_service)

        for enabled_service in ENABLED_SERVICES:
            self.run_cli_cmd('property set enable_%s yes' % enabled_service)

        predeploy_cmds = test_config.get_predeploy_cmds()
        for predeploy_cmd in predeploy_cmds:
            self.run_cli_cmd('%s' % predeploy_cmd)

        # deploy limited services openstack
        msg = self.run_cli_cmd('deploy -v')
        self.log.info(msg)

        docker_ps = test_config.run_remote_cmd('docker ps', hostname)
        docker_ps = docker_ps.replace('\r', '\n')
        for disabled_service in DISABLED_SERVICES:
            self.assertNotIn(disabled_service, docker_ps,
                             'disabled service: %s ' % disabled_service +
                             'is running on host: %s ' % hostname +
                             'after deploy.')

        for enabled_service in ENABLED_SERVICES:
            self.assertIn(enabled_service, docker_ps,
                          'enabled service: %s ' % enabled_service +
                          'is not running on host: %s ' % hostname +
                          'after deploy.')

        # destroy services
        self.run_cli_cmd('host destroy %s' % hostname)

        docker_ps = test_config.run_remote_cmd('docker ps', hostname)
        for disabled_service in DISABLED_SERVICES:
            self.assertNotIn(disabled_service, docker_ps,
                             'disabled service: %s ' % disabled_service +
                             'is running on host: %s ' % hostname +
                             'after destroy.')

        for enabled_service in ENABLED_SERVICES:
            self.assertNotIn(enabled_service, docker_ps,
                             'enabled service: %s ' % enabled_service +
                             'is still running on host: %s ' % hostname +
                             'after destroy.')

    def tearDown(self):
        # re-enabled disabled services
        for disabled_service in DISABLED_SERVICES:
            self.run_cli_cmd('property set enable_%s yes' % disabled_service)

        super(KollaCliTest, self).tearDown()


if __name__ == '__main__':
    unittest.main()
