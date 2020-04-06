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

import unittest

CLIENT = ClientApi()


class TestFunctional(KollaCliTest):

    def test_reconfigure(self):
        # test will start with no hosts in the inventory
        # reconfigure will throw an exception if it fails
        # disable all services first as without it empty groups cause errors
        enable_service_props = {}
        for service in CLIENT.service_get_all():
            service_name = service.name.replace('-', '_')
            enable_service_props['enable_%s' % service_name] = 'no'
        CLIENT.property_set(enable_service_props)

        msg = ''
        try:
            job = CLIENT.reconfigure()
            job.wait()
            msg = job.get_console_output()
            self.assertEqual(job.get_status(), 0,
                             'error performing reconfigure: %s' % msg)
        except Exception as e:
            self.assertEqual(0, 1,
                             'unexpected exception in reconfigure %s, %s'
                             % (e.message, msg))


if __name__ == '__main__':
    unittest.main()
