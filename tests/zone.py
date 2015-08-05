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
from common import KollaClientTest
import unittest


class TestFunctional(KollaClientTest):

    def test_zone_add_remove(self):
        msg = self.run_client_cmd('zone list')
        self.assertEqual('', msg.strip(), 'zone list output is not empty: %s'
                         % msg)

        zone1 = 'zone_test1'
        self.run_client_cmd('zone add %s' % zone1)

        msg = self.run_client_cmd('zone list')
        self.assertEqual(zone1, msg.strip(), 'zone: %s not in cli output: %s'
                         % (zone1, msg))

        zone2 = 'zone_test2'
        self.run_client_cmd('zone add %s' % zone2)

        msg = self.run_client_cmd('zone list')
        exp_out = ('%s, %s' % (zone1, zone2))
        self.assertEqual(exp_out, msg.strip(),
                         'zones: %s & %s not in cli output: %s'
                         % (zone1, zone2, msg))

        self.run_client_cmd('zone remove %s' % zone2)

        msg = self.run_client_cmd('zone list')
        self.assertEqual(zone1, msg.strip())

        self.run_client_cmd('zone remove %s' % zone1)

        msg = self.run_client_cmd('zone list')
        self.assertEqual('', msg.strip())

if __name__ == '__main__':
    unittest.main()
