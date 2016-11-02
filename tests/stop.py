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

from kollacli.api.client import ClientApi

import unittest

TEST_GROUP_NAME = 'test_group'
CLIENT = ClientApi()

NOT_KNOWN = 'Name or service not known'
UNREACHABLE = 'Status: unreachable'

ENABLED_SERVICES = [
    'rabbitmq'
    ]

# after deploy
EXPECTED_CONTAINERS_1 = [
    'rabbitmq'
    ]


class TestFunctional(KollaCliTest):

    def test_stop(self):
        test_config = TestConfig()
        test_config.load()

        # add host to inventory
        hostnames = test_config.get_hostnames()
        if hostnames:
            is_physical_host = True
            pwd = test_config.get_password(hostnames[0])
        else:
            # No physical hosts in config, use a non-existent host.
            # This will generate expected exceptions in all host access
            # commands.
            hostnames = ['test_deploy_host1']
            is_physical_host = False
            pwd = 'test_pwd'

        CLIENT.host_add(hostnames)

        try:
            setup_info = {}
            for hostname in hostnames:
                setup_info[hostname] = {'password': pwd}
            CLIENT.host_setup(setup_info)
        except Exception as e:
            self.assertFalse(is_physical_host, 'host setup exception: %s' % e)
            self.assertIn(NOT_KNOWN, '%s' % e,
                          'Unexpected exception in host setup: %s' % e)

        # add host to a new deploy group
        CLIENT.group_add([TEST_GROUP_NAME])
        group = CLIENT.group_get([TEST_GROUP_NAME])[0]
        for hostname in hostnames:
            group.add_host(hostname)
        # due to required host to group association where there are enabled
        # services and we have only one host, move the enabled services
        # out of control over to the new group, then move them back to
        # control once we are done
        control = CLIENT.group_get(['control'])[0]
        for servicename in control.get_services():
            if servicename in ENABLED_SERVICES:
                control.remove_service(servicename)
                group.add_service(servicename)

        # stop services, initialize server
        self.log.info('Start stop #1')
        job = CLIENT.async_host_stop(hostnames)
        self._process_job(job, 'stop #1', is_physical_host)

        self.log.info('updating various properties for the test')

        # disable most services so the test is quicker
        enable_service_props = {}
        for service in CLIENT.service_get_all():
            if service.get_parent():
                # skip subservices
                continue
            enable = 'no'
            if service.name in ENABLED_SERVICES:
                enable = 'yes'
            enable_service_props['enable_%s' % service.name] = enable
        CLIENT.property_set(enable_service_props)

        predeploy_cmds = test_config.get_predeploy_cmds()
        for predeploy_cmd in predeploy_cmds:
            self.run_cli_cmd('%s' % predeploy_cmd)

        # do a deploy of a limited set of services
        self.log.info('Start a deployment')
        job = CLIENT.async_deploy()
        self._process_job(job, 'deploy', is_physical_host)

        if is_physical_host:
            docker_ps = test_config.run_remote_cmd('docker ps', hostname)
            docker_ps = docker_ps.replace('\r', '\n')
            for service in CLIENT.service_get_all():
                if service.name not in ENABLED_SERVICES:
                    self.assertNotIn(service.name, docker_ps,
                                     'disabled service: %s ' % service.name +
                                     'is running on host: %s ' % hostname +
                                     'after deploy.')
            for servicename in EXPECTED_CONTAINERS_1:
                self.assertIn(servicename, docker_ps,
                              'enabled service: %s ' % servicename +
                              'is not running on host: %s ' % hostname +
                              'after deploy.')

        self.log.info('Start stop #2')
        job = CLIENT.async_host_stop(hostnames)
        self._process_job(job, 'stop #2', is_physical_host)

        if is_physical_host:
            docker_ps = test_config.run_remote_cmd('docker ps', hostname)
            for service in CLIENT.service_get_all():
                if service.name not in ENABLED_SERVICES:
                    self.assertNotIn(service.name, docker_ps,
                                     'disabled service: %s ' % service.name +
                                     'is running on host: %s ' % hostname +
                                     'after stop.')

    def _process_job(self, job, descr, is_physical_host, expect_kill=False):
        status = job.wait()
        err_msg = job.get_error_message()
        self.log.info('job is complete. status: %s, err: %s'
                      % (status, err_msg))
        if expect_kill:
            self.assertEqual(2, status, 'Job %s does not have killed status %s'
                             % (descr, err_msg))
        else:
            if is_physical_host:
                self.assertEqual(0, status, 'Job %s failed: %s'
                                 % (descr, err_msg))
            else:
                self.assertEqual(1, status, 'Job %s ' % descr +
                                 'succeeded when it should have failed')
                self.assertIn(UNREACHABLE,
                              'Job %s: No hosts, but got wrong error: %s'
                              % (descr, err_msg))

if __name__ == '__main__':
    unittest.main()
