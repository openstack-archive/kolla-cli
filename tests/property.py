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

import os
import unittest

from kollacli.common.utils import get_kolla_etc


class TestFunctional(KollaCliTest):

    def test_property_set_clear(self):
        # test list

        # This test should leave the globals.yml file unchanged
        # after the test completes.
        globals_path = os.path.join(get_kolla_etc(), 'globals.yml')
        size_start = os.path.getsize(globals_path)

        msg = self.run_cli_cmd('property list')
        key = 'kolla_base_distro'
        value = 'ol'
        ok = self._property_value_exists(key, value, msg)
        self.assertTrue(ok, 'property not in output: %s, %s' % (key, value))

        # test append
        key = 'TeStKeY'
        value = 'TeStVaLuE'
        self.run_cli_cmd('property set %s %s' % (key, value))
        msg = self.run_cli_cmd('property list')
        ok = self._property_value_exists(key, value, msg)
        self.assertTrue(ok, 'set failed property not in output: %s, %s' %
                        (key, value))

        # test modify existing
        key = 'TeStKeY'
        value = 'TeStVaLuE2'
        self.run_cli_cmd('property set %s %s' % (key, value))
        msg = self.run_cli_cmd('property list')
        ok = self._property_value_exists(key, value, msg)
        self.assertTrue(ok, 'set failed property not in output: %s, %s' %
                        (key, value))

        # test clear
        key = 'TeStKeY'
        value = 'TeStVaLuE2'
        self.run_cli_cmd('property clear %s' % key)
        msg = self.run_cli_cmd('property list')
        ok = self._property_value_exists(key, value, msg)
        self.assertFalse(ok, 'clear failed property in output: %s, %s' %
                         (key, value))

        # check that globals.yml file size didn't change
        size_end = os.path.getsize(globals_path)
        self.assertEqual(size_start, size_end, 'globals.yml size changed ' +
                         'from %s to %s' % (size_start, size_end))

    def _property_value_exists(self, key, value, cli_output):
        """Verify cli data against model data"""
        # check for any host in cli output that shouldn't be there
        cli_lines = cli_output.split('\n')
        for cli_line in cli_lines:
            if key in cli_line and value in cli_line:
                return True
        return False

if __name__ == '__main__':
    unittest.main()
