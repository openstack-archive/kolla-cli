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
from common import DISABLED_SERVICES
from common import ENABLED_DATA_SERVICES
from common import ENABLED_SERVICES
from common import KollaCliTest
from common import TestConfig
from common import UNKNOWN_HOST

import unittest

TEST_GROUP_NAME = 'test_group'


class TestFunctional(KollaCliTest):

    def test_destroy(self):
        test_config = TestConfig()
        test_config.load()

        # add host to inventory
        hostnames = test_config.get_hostnames()
        if hostnames:
            hostname = test_config.get_hostnames()[0]
            is_physical_host = True
            pwd = test_config.get_password(hostname)
        else:
            # No physical hosts in config, use a non-existent host.
            # This will generate expected exceptions in all host access
            # commands.
            hostname = 'test_deploy_host1'
            is_physical_host = False
            pwd = 'test_pwd'

        self.run_cli_cmd('host add %s' % hostname)

        try:
            self.run_cli_cmd('host setup %s --insecure %s'
                             % (hostname, pwd))
        except Exception as e:
            self.assertFalse(is_physical_host, 'host setup exception: %s' % e)
            self.assertIn(UNKNOWN_HOST, '%s' % e,
                          'Unexpected exception in host setup: %s' % e)

        # add host to a new deploy group
        self.run_cli_cmd('group add %s' % TEST_GROUP_NAME)
        self.run_cli_cmd('group addhost %s %s' % (TEST_GROUP_NAME, hostname))
        # due to required host to group association where there are enabled
        # services and we have only one host, move the enabled services
        # out of control over to the new group, then move them back to
        # control once we are done
        for service in ENABLED_SERVICES:
            self.run_cli_cmd('service removegroup %s control' % service)
            self.run_cli_cmd('service addgroup %s %s' %
                             (service, TEST_GROUP_NAME))

        # destroy services, initialize server
        try:
            self.run_cli_cmd('host destroy %s --includedata' % hostname)
        except Exception as e:
            self.assertFalse(is_physical_host, '1st destroy exception: %s' % e)
            self.assertIn(UNKNOWN_HOST, '%s' % e,
                          'Unexpected exception in 1st destroy: %s' % e)

        # disable most services so the test is quicker
        for disabled_service in DISABLED_SERVICES:
            self.run_cli_cmd('property set enable_%s no' % disabled_service)

        for enabled_service in ENABLED_SERVICES:
            self.run_cli_cmd('property set enable_%s yes' % enabled_service)

        predeploy_cmds = test_config.get_predeploy_cmds()
        for predeploy_cmd in predeploy_cmds:
            self.run_cli_cmd('%s' % predeploy_cmd)

        # deploy limited services openstack
        try:
            msg = self.run_cli_cmd('deploy -v')
            self.log.info(msg)
        except Exception as e:
            self.assertFalse(is_physical_host, 'deploy exception: %s' % e)
            self.assertIn(UNKNOWN_HOST, '%s' % e,
                          'Unexpected exception in deploy: %s' % e)

        if is_physical_host:
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

        # destroy non-data services (via --stop flag)
        # this should leave only data containers running
        try:
            self.run_cli_cmd('host destroy %s --stop -v' % hostname)
        except Exception as e:
            self.assertFalse(is_physical_host, '2nd destroy exception: %s' % e)
            self.assertIn(UNKNOWN_HOST, '%s' % e,
                          'Unexpected exception in 2nd destroy: %s' % e)

        if is_physical_host:
            docker_ps = test_config.run_remote_cmd('docker ps', hostname)
            for disabled_service in DISABLED_SERVICES:
                self.assertNotIn(disabled_service, docker_ps,
                                 'disabled service: %s ' % disabled_service +
                                 'is running on host: %s ' % hostname +
                                 'after destroy.')

            for enabled_service in ENABLED_DATA_SERVICES:
                self.assertIn(enabled_service, docker_ps,
                              'enabled service: %s ' % enabled_service +
                              'is not running on host: %s ' % hostname +
                              'after no-data destroy.')

        try:
            self.run_cli_cmd('host destroy %s --includedata --stop -vv'
                             % hostname)
        except Exception as e:
            self.assertFalse(is_physical_host, '3rd destroy exception: %s' % e)
            self.assertIn(UNKNOWN_HOST, '%s' % e,
                          'Unexpected exception in 3rd destroy: %s' % e)

        if is_physical_host:
            docker_ps = test_config.run_remote_cmd('docker ps', hostname)
            for disabled_service in DISABLED_SERVICES:
                self.assertNotIn(disabled_service, docker_ps,
                                 'disabled service: %s ' % disabled_service +
                                 'is running on host: %s ' % hostname +
                                 'after destroy.')

            for enabled_service in ENABLED_DATA_SERVICES:
                self.assertNotIn(enabled_service, docker_ps,
                                 'enabled service: %s ' % enabled_service +
                                 'is running on host: %s ' % hostname +
                                 'after destroy.')

            for enabled_service in ENABLED_SERVICES:
                self.assertNotIn(enabled_service, docker_ps,
                                 'enabled service: %s ' % enabled_service +
                                 'is running on host: %s ' % hostname +
                                 'after destroy.')

if __name__ == '__main__':
    unittest.main()
