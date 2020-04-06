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

from kolla_cli.api.client import ClientApi

import random
import time
import unittest

TEST_GROUP_NAME = 'test_group'
CLIENT = ClientApi()

NOT_KNOWN = 'Name or service not known'
UNREACHABLE = 'UNREACHABLE!'


class TestFunctional(KollaCliTest):

    def test_destroy(self):

        # use a non-existent host.
        # This will generate expected exceptions in all host access
        # commands.
        hostnames = ['test_deploy_host1']
        CLIENT.host_add(hostnames)

        # add host to a new deploy group
        CLIENT.group_add([TEST_GROUP_NAME])
        group = CLIENT.group_get([TEST_GROUP_NAME])[0]
        for hostname in hostnames:
            group.add_host(hostname)

        # destroy services, initialize server
        self.log.info('Start destroy #1')
        job = CLIENT.host_destroy(hostnames, destroy_type='kill',
                                  include_data=True, verbose_level=2)
        self._process_job(job, 'destroy #1')

        self.log.info('updating various properties for the test')

        # the following deploy will fail if we don't disable all the
        # services first
        enable_service_props = {}
        for service in CLIENT.service_get_all():
            service_name = service.name.replace('-', '_')
            enable_service_props['enable_%s' % service_name] = 'no'
        CLIENT.property_set(enable_service_props)

        # test killing a deploy
        self.log.info('Kill a deployment')
        job = CLIENT.deploy()
        time.sleep(random.randint(5, 8))
        job.kill()
        self._process_job(job, 'deploy-kill',
                          expect_kill=True)

        # do a deploy of a limited set of services
        self.log.info('Start a deployment')
        job = CLIENT.deploy()
        self._process_job(job, 'deploy')

        self.log.info('Start destroy #3, include data')
        job = CLIENT.host_destroy(hostnames, destroy_type='stop',
                                  include_data=True)
        self._process_job(job, 'destroy #3')

    def _process_job(self, job, descr, expect_kill=False):
        status = job.wait()
        output = job.get_console_output()
        self.log.info('job is complete. status: %s, err: %s'
                      % (status, output))
        if expect_kill:
            self.assertEqual(2, status, 'Job %s does not have killed status %s'
                             % (descr, output))
        else:
            self.assertEqual(1, status, 'Job %s ' % descr +
                             'succeeded when it should have failed')
            self.assertIn(UNREACHABLE, output,
                          'Job %s: No hosts, but got wrong error: %s'
                          % (descr, output))


if __name__ == '__main__':
    unittest.main()
