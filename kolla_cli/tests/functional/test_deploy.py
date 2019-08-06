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
from kolla_cli.common.ansible_inventory import AnsibleInventory
from kolla_cli.common.inventory import Inventory

import json
import unittest

CLIENT = ClientApi()
UNREACHABLE = 'UNREACHABLE!'


class TestFunctional(KollaCliTest):

    def test_json_generator(self):
        self.run_cli_cmd('setdeploy local')

        host1 = 'host_test1'
        self.run_cli_cmd('host add %s' % host1)

        inventory = Inventory.load()

        path = inventory.create_json_gen_file()
        (retval, msg) = self.run_command(path)
        inventory.remove_json_gen_file(path)
        self.assertEqual(0, retval, 'json generator command failed: %s' % msg)

        self.assertNotEqual('', msg, 'json generator returned no data: %s'
                            % msg)

        self.assertIn(host1, msg, '%s not in json_gen output: %s'
                      % (host1, msg))

        ansible_inventory = AnsibleInventory()
        services = ansible_inventory.services
        for servicename, service in services.items():
            self.assertIn(servicename, msg, '%s not in json_gen output: %s'
                          % (servicename, msg))

        # verify that json output is valid. This will throw if invalid json
        try:
            json.loads(msg)
        except Exception:
            self.assertTrue(False, 'invalid json: %s' % msg)
        remote_msg = '"ansible_ssh_user": "root"'
        local_msg = '"ansible_connection": "local"'

        # verify that setdeploy local worked:
        self.assertIn(local_msg, msg, '%s not in local json_gen output: %s'
                      % (local_msg, msg))
        self.assertNotIn(remote_msg, msg, '%s in local json_gen output: %s'
                         % (remote_msg, msg))

        # verify that setdeploy remote worked:
        CLIENT.set_deploy_mode(remote_mode=True)
        inventory = Inventory.load()
        path = inventory.create_json_gen_file()
        (retval, msg) = self.run_command(path)
        inventory.remove_json_gen_file(path)
        self.assertEqual(0, retval, 'json generator command failed: %s' % msg)

        self.assertIn(remote_msg, msg, '%s not in remote json_gen output: %s'
                      % (remote_msg, msg))
        self.assertNotIn(local_msg, msg, '%s in remote json_gen output: %s'
                         % (local_msg, msg))

    def test_json_filtering(self):

        hosts = ['host_test1', 'host_test2', 'host_test3']
        groups = ['control', 'network', 'storage']

        for host in hosts:
            self.run_cli_cmd('host add %s' % host)
            for groupname in groups:
                group = CLIENT.group_get([groupname])[0]
                group.add_host(host)

        inventory = Inventory.load()

        # filter by host- include all hosts
        inv_filter = {'deploy_hosts': hosts}
        path = inventory.create_json_gen_file(inv_filter)
        self.log.info('run command: %s' % path)
        (retval, msg) = self.run_command(path)
        inventory.remove_json_gen_file(path)
        self.assertEqual(0, retval, 'json generator command failed: %s' % msg)

        self.check_json(msg, groups, hosts, groups, hosts)

        # filter by host- to first host
        included_host = hosts[0]
        inv_filter = {'deploy_hosts': [included_host]}
        path = inventory.create_json_gen_file(inv_filter)
        self.log.info('run command: %s' % path)
        (retval, msg) = self.run_command(path)
        inventory.remove_json_gen_file(path)
        self.assertEqual(0, retval, 'json generator command failed: %s' % msg)
        self.check_json(msg, groups, hosts, groups, [included_host])

        # filter by group- include all groups
        inv_filter = {'deploy_groups': groups}
        path = inventory.create_json_gen_file(inv_filter)
        self.log.info('run command: %s' % path)
        (retval, msg) = self.run_command(path)
        inventory.remove_json_gen_file(path)
        self.assertEqual(0, retval, 'json generator command failed: %s' % msg)
        self.check_json(msg, groups, hosts, groups, hosts)

        # filter by group- to first group
        included_group = groups[0]
        inv_filter = {'deploy_groups': [included_group]}
        path = inventory.create_json_gen_file(inv_filter)
        self.log.info('run command: %s' % path)
        (retval, msg) = self.run_command(path)
        inventory.remove_json_gen_file(path)
        self.assertEqual(0, retval, 'json generator command failed: %s' % msg)
        self.check_json(msg, groups, hosts, [included_group], hosts)

    def test_deploy(self):
        # test will start with no hosts in the inventory
        # deploy will throw an exception if it fails
        # disable all services first as without it empty groups cause errors
        enable_service_props = {}
        for service in CLIENT.service_get_all():
            service_name = service.name.replace('-', '_')
            enable_service_props['enable_%s' % service_name] = 'no'
        CLIENT.property_set(enable_service_props)

        msg = ''
        CLIENT.set_deploy_mode(remote_mode=False)
        job = CLIENT.deploy(hostnames=[])
        job.wait()
        msg = job.get_console_output()
        self.assertEqual(job.get_status(), 0,
                         'error performing whole host deploy %s' % msg)

        # test deploy with timeout
        msg = self.run_cli_cmd('action deploy --timeout .001',
                               expect_error=True)
        self.assertIn('timed out', msg)

    def test_upgrade(self):
        # test will upgrade an environment with no hosts, mostly a NOP,
        # but it will go through the client code paths.
        self.run_cli_cmd('action upgrade -v')

        msg = ''
        # run rabbitmq service deploy
        try:
            CLIENT.host_add(['dummy_host'])
            CLIENT.set_deploy_mode(remote_mode=True)
            job = CLIENT.upgrade()
            job.wait()
            msg = job.get_console_output()
            self.assertEqual(job.get_status(), 1,
                             'upgrade succeeded unexpectedly: %s'
                             % msg)
            self.assertIn(UNREACHABLE, msg)
        except Exception as e:
            raise e
        finally:
            CLIENT.host_remove(['dummy_host'])

    def test_pull(self):
        # test will upgrade an environment with no hosts, mostly a NOP,
        # but it will go through the client code paths.
        self.run_cli_cmd('action pull -v')

        CLIENT.host_add(['test_pull_host'])
        CLIENT.set_deploy_mode(remote_mode=True)
        job = CLIENT.pull()
        job.wait()
        msg = job.get_console_output()
        self.assertEqual(job.get_status(), 1,
                         'pull succeeded unexpectedly: %s'
                         % msg)
        self.assertIn(UNREACHABLE, msg)

    def check_json(self, msg, groups, hosts, included_groups, included_hosts):
        err_msg = ('included groups: %s\n' % included_groups +
                   'included hosts: %s\n' % included_hosts)
        inv_dict = json.loads(msg)
        for group in groups:
            group_hosts = inv_dict[group]['hosts']
            for host in hosts:
                if group in included_groups and host in included_hosts:
                    self.assertIn(host, group_hosts, err_msg +
                                  '%s not in %s' % (host, group_hosts))
                else:
                    self.assertNotIn(host, group_hosts, err_msg +
                                     '%s still in %s' % (host, group_hosts))


if __name__ == '__main__':
    unittest.main()
