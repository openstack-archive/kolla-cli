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

from kollacli.ansible import inventory

import json
import os
import unittest

JSON_GENPATH = '/usr/share/kolla/kollacli/tools/json_generator.py'


class TestFunctional(KollaCliTest):

    def test_json_generator(self):
        self.run_cli_cmd('setdeploy local')

        host1 = 'host_test1'
        self.run_cli_cmd('host add %s' % host1)

        (retval, msg) = self.run_command(JSON_GENPATH)
        self.assertEqual(0, retval, 'json generator command failed: %s' % msg)

        self.assertNotEqual('', msg, 'json generator returned no data: %s'
                            % msg)

        self.assertIn(host1, msg, '%s not in json_gen output: %s'
                      % (host1, msg))

        for service, subservices in inventory.SERVICES.items():
            self.assertIn(service, msg, '%s not in json_gen output: %s'
                          % (service, msg))
            for subservice in subservices:
                self.assertIn(subservice, msg, '%s not in json_gen output: %s'
                              % (subservice, msg))

        # verify that json output is valid. This will throw if invalid json
        json.loads(msg)

        remote_msg = '"ansible_ssh_user": "kolla"'
        local_msg = '"ansible_connection": "local"'

        # verify that setdeploy local worked:
        self.assertIn(local_msg, msg, '%s not in local json_gen output: %s'
                      % (local_msg, msg))
        self.assertNotIn(remote_msg, msg, '%s in local json_gen output: %s'
                         % (remote_msg, msg))

        # verify that setdeploy remote worked:
        self.run_cli_cmd('setdeploy remote')
        (retval, msg) = self.run_command(JSON_GENPATH)
        self.assertEqual(0, retval, 'json generator command failed: %s' % msg)

        self.assertIn(remote_msg, msg, '%s not in remote json_gen output: %s'
                      % (remote_msg, msg))
        self.assertNotIn(local_msg, msg, '%s in remote json_gen output: %s'
                         % (local_msg, msg))

    def test_simple_deploy(self):
        # test will start with no hosts in the inventory
        # deploy will throw an exception if it fails
        self.run_cli_cmd('deploy')

        # quick check of kollacli dump
        # dump successful to /tmp/kollacli_dump_Umxu6d.tgz
        msg = self.run_cli_cmd('dump')
        self.assertIn('/', msg, 'path not found in dump output: %s' % msg)

        dump_path = '/' + msg.strip().split('/', 1)[1]
        is_file = os.path.isfile(dump_path)
        self.assertTrue(is_file,
                        'dump file not found at %s' % dump_path)


if __name__ == '__main__':
    unittest.main()
