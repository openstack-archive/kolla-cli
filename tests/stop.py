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

from kollacli.api.client import ClientApi

import unittest

TEST_GROUP_NAME = 'test_group'
CLIENT = ClientApi()

NOT_KNOWN = 'Name or service not known'
UNREACHABLE = 'Status: unreachable'


class TestFunctional(KollaCliTest):

    def test_stop(self):
        # No physical hosts in config, use a non-existent host.
        # This will generate expected exceptions in all host access
        # commands.
        hostnames = ['test_deploy_host1']
        pwd = 'test_pwd'

        CLIENT.host_add(hostnames)

        try:
            setup_info = {}
            for hostname in hostnames:
                setup_info[hostname] = {'password': pwd}
            CLIENT.host_setup(setup_info)
        except Exception as e:
            self.assertFalse(False, 'host setup exception: %s' % e)
            self.assertIn(NOT_KNOWN, '%s' % e,
                          'Unexpected exception in host setup: %s' % e)

        # add host to a new deploy group
        CLIENT.group_add([TEST_GROUP_NAME])
        group = CLIENT.group_get([TEST_GROUP_NAME])[0]
        for hostname in hostnames:
            group.add_host(hostname)

        # stop services, initialize server
        self.log.info('Start stop #1')
        job = CLIENT.host_stop(hostnames)
        self._process_job(job, 'stop #1')

        self.log.info('updating various properties for the test')

        # disable services so the test is quicker
        enable_service_props = {}
        for service in CLIENT.service_get_all():
            service_name = service.name.replace('-', '_')
            enable_service_props['enable_%s' % service_name] = 'no'
        CLIENT.property_set(enable_service_props)

        # do a deploy of a limited set of services
        self.log.info('Start a deployment')
        job = CLIENT.deploy()
        self._process_job(job, 'deploy')

        self.log.info('Start stop #2')
        job = CLIENT.host_stop(hostnames)
        self._process_job(job, 'stop #2')

    def _process_job(self, job, descr, expect_kill=False):
        status = job.wait()
        err_msg = job.get_error_message()
        self.log.info('job is complete. status: %s, err: %s'
                      % (status, err_msg))
        if expect_kill:
            self.assertEqual(2, status, 'Job %s does not have killed status %s'
                             % (descr, err_msg))
        else:
            self.assertEqual(1, status, 'Job %s ' % descr +
                             'succeeded when it should have failed')
            self.assertIn(UNREACHABLE,
                          'Job %s: No hosts, but got wrong error: %s'
                          % (descr, err_msg))

if __name__ == '__main__':
    unittest.main()
