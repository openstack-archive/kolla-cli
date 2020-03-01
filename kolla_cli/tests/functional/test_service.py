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

import json
import unittest

from kolla_cli.api.client import ClientApi
from kolla_cli.common.ansible_inventory import AnsibleInventory
from kolla_cli.common.inventory import Inventory

CLIENT = ClientApi()


class TestFunctional(KollaCliTest):

    def test_service_api(self):
        service1 = 'nova'
        service2 = 'nova-api'
        exp_services = sorted([service1, service1, service2])
        servicenames = []
        services = CLIENT.service_get(exp_services)
        for service in services:
            servicenames.append(service.name)
        servicenames = sorted(servicenames)
        self.assertEqual(exp_services, servicenames, 'services mis-match')

    def test_service_list(self):
        """$ kolla-cli service list -f json

        [{"Service": "barbican", "Children": ["barbican-keystone-listener"
        "barbican-worker", "barbican-api"]}, {"Service": "barbican-api"
        "Children": []}, {"Service": "barbican-keystone-listener",
        "Children": []}, {"Service": "barbican-worker"...]
        """
        msg = self.run_cli_cmd('service list -f json')
        cli_services = json.loads(msg)
        ansible_inventory = AnsibleInventory()
        ansible_inventory_services = []
        ansible_inventory_service_names = []
        for service in ansible_inventory.services.values():
            if service.is_supported():
                ansible_inventory_services.append(service)
                ansible_inventory_service_names.append(service.name)
        num_services = len(ansible_inventory_services)
        self.assertEqual(num_services, len(cli_services),
                         '# of cli services != expected services.' +
                         '\n\nexpected services: %s'
                         % ansible_inventory_service_names +
                         '\n\ncli services: %s' % cli_services)

    def test_listgroups(self):
        """$ kolla-cli service listgroups

        +------------------------+-------------------------+ \
        | Service                | Groups                  | \
        +------------------------+-------------------------+ \
        | cinder                 | ['control', 'control2'] | \
        | cinder-api             |                         | \
        | cinder-backup          | ['storage']             | \
        | cinder-scheduler       |                         | \
        | cinder-volume          | ['storage']             | \
        | glance                 | ['control', 'control2'] | \
        | glance-api             |                         | \
        | glance-registry        |                         | \
        ...

        """
        msg = self.run_cli_cmd('service listgroups -f json')
        cli_services = json.loads(msg)

        ansible_inventory = AnsibleInventory()
        ansible_inventory_services = []
        ansible_inventory_service_names = []
        for service in ansible_inventory.services.values():
            if service.is_supported():
                ansible_inventory_services.append(service)
                ansible_inventory_service_names.append(service.name)
        num_services = len(ansible_inventory_services)
        self.assertEqual(num_services, len(cli_services),
                         '# of cli services (%s) ' % len(cli_services) +
                         '!= # of expected services (%s).' % num_services +
                         '\n\ncli services: %s' % cli_services)

    def test_service_add_group(self):
        servicename = 'cinder'
        new_group = 'network'

        inventory = Inventory.load()
        service = inventory.get_service(servicename)
        groupnames = service.get_groupnames()

        # add new group to a service
        self.run_cli_cmd('service addgroup %s %s' % (servicename, new_group))

        msg = self.run_cli_cmd('service listgroups -f json')
        cli_services = json.loads(msg)
        cli_service = ''
        for svc in cli_services:
            if svc['Service'] == servicename:
                cli_service = svc
                break
        self.assertNotEqual(cli_service, '',
                            'service: %s, ' % servicename +
                            'not found in cli_services: \n%s'
                            % cli_service)
        cli_groups = cli_service['Groups']
        groupnames.append(new_group)
        self.assertEqual(groupnames, cli_groups,
                         'service: %s, ' % service +
                         'expected groups: %s, ' % groupnames +
                         'cli_groups: %s' % cli_groups)

        # remove that group
        self.run_cli_cmd('service removegroup %s %s' % (servicename,
                                                        new_group))
        groupnames.remove(new_group)

        msg = self.run_cli_cmd('service listgroups -f json')
        cli_services = json.loads(msg)
        for svc in cli_services:
            if svc['Service'] == servicename:
                cli_service = svc
                break
        self.assertNotEqual(cli_service, '',
                            'service: %s, ' % servicename +
                            'not found in cli_services: \n%s'
                            % cli_service)
        cli_groups = cli_service['Groups']
        expected_groups = groupnames
        self.assertEqual(expected_groups, cli_groups,
                         'service: %s, ' % service +
                         'expected groups: %s, ' % expected_groups +
                         'cli_groups: %s' % cli_groups)

        # add new group to a service which has a parent
        servicename = 'glance-api'
        new_group = 'control'
        self.run_cli_cmd('service addgroup %s %s' % (servicename, new_group))

        msg = self.run_cli_cmd('service listgroups -f json')
        cli_services = json.loads(msg)
        for svc in cli_services:
            if svc['Service'] == servicename:
                cli_service = svc
                break
        self.assertNotEqual(cli_service, '',
                            'service: %s, ' % servicename +
                            'not found in cli_services: \n%s'
                            % cli_service)
        cli_groups = cli_service['Groups']
        expected_groups = ['%s' % new_group]
        self.assertEqual(expected_groups, cli_groups,
                         'service: %s, ' % service +
                         'expected groups: %s, ' % expected_groups +
                         'cli_groups: %s' % cli_groups)

        # remove that group
        self.run_cli_cmd('service removegroup %s %s' % (servicename,
                                                        new_group))

        msg = self.run_cli_cmd('service listgroups -f json')
        cli_services = json.loads(msg)
        for svc in cli_services:
            if svc['Service'] == servicename:
                cli_service = svc
                break
        self.assertNotEqual(cli_service, '',
                            'service: %s, ' % service +
                            'not found in cli_services: \n%s'
                            % cli_service)
        cli_groups = cli_service['Groups']
        expected_groups = []
        self.assertEqual(expected_groups, cli_groups,
                         'service: %s, ' % servicename +
                         'expected groups: %s, ' % expected_groups +
                         'cli_groups: %s' % cli_groups)

        test_group = 'testgroup'
        self.run_cli_cmd('group add %s' % test_group)
        self.run_cli_cmd('service addgroup cinder %s' % test_group)
        self.run_cli_cmd('group remove %s' % test_group)
        msg = self.run_cli_cmd('service listgroups -f json')
        self.assertNotIn(test_group, msg,
                         'Group: %s, still listed in services: %s'
                         % (test_group, msg))


if __name__ == '__main__':
    unittest.main()
