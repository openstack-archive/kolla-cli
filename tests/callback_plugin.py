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

from kollacli.api.client import ClientApi

import unittest

CLIENT = ClientApi()

NOT_KNOWN = 'Name or service not known'
UNREACHABLE = 'Status: unreachable'


class TestFunctional(KollaCliTest):

    def test_callback(self):
        """callback test

        This test is disabled by default because it takes too long to run.
        To enable it, remove the 'x' from the method name.
        """
        CLIENT.host_add(['localhost'])

        # add host to group
        CLIENT.group_add(['control'])
        groups = CLIENT.group_get_all()
        for group in groups:
                group.add_host('localhost')

        self.log.info('Start a deployment')
        job = CLIENT.deploy()

        time.sleep(20)
        self.log.info('\nwaking up from sleep............................\n')
        job.wait()

        self.log.info('deploy complete')

if __name__ == '__main__':
    unittest.main()
