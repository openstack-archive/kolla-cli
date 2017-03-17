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
import time

from common import KollaCliTest
from common import TestConfig

from kollacli.api.client import ClientApi

import unittest

CLIENT = ClientApi()

NOT_KNOWN = 'Name or service not known'
UNREACHABLE = 'Status: unreachable'


class TestFunctional(KollaCliTest):

    def xtest_callback(self):
        """callback test

        This test is disabled by default because it takes too long to run.
        To enable it, remove the 'x' from the method name.
        """
        test_config = TestConfig()
        test_config.load()

        # add host to inventory
        hostnames = test_config.get_hostnames()
        if hostnames:
            pwd = test_config.get_password(hostnames[0])
        else:
            # No physical hosts in config, use a non-existent host.
            # This will generate expected exceptions in all host access
            # commands.
            self.log.info('No hosts, skipping test')
            return

        CLIENT.host_add(hostnames)

        try:
            setup_info = {}
            for hostname in hostnames:
                setup_info[hostname] = {'password': pwd}
            CLIENT.host_setup(setup_info)
        except Exception as e:
            self.assertIn(NOT_KNOWN, '%s' % e,
                          'Unexpected exception in host setup: %s' % e)

        # add host to group
        CLIENT.group_add(['control'])
        groups = CLIENT.group_get_all()
        for group in groups:
            for hostname in hostnames:
                group.add_host(hostname)

        self.log.info('Start a deployment')
        job = CLIENT.deploy()

        time.sleep(120)
        self.log.info('\nwaking up from sleep............................\n')
        job.wait()

        self.log.info('deploy complete')


if __name__ == '__main__':
    unittest.main()
