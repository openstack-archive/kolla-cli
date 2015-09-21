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

import json
import unittest

from kollacli.ansible.inventory import DEFAULT_GROUPS
from kollacli.ansible.inventory import DEFAULT_OVERRIDES
from kollacli.ansible.inventory import SERVICES


class TestFunctional(KollaCliTest):

    def test_service_lists(self):
        """$ kollacli service list

        +--------------+-----------------------------------------------------+
        | Service      | Sub-Services                                        |
        +--------------+-----------------------------------------------------+
        | cinder       | ['cinder-api', 'cinder-scheduler', 'cinder-backup', |
        | glance       | ['glance-api', 'glance-registry']                   |
        | haproxy      | []                                                  |
        """
        msg = self.run_cli_cmd('service list -f json')
        cli_services = json.loads(msg)
        self.assertEqual(len(SERVICES), len(cli_services),
                         '# of cli services != expected services.' +
                         '\n\nexpected services: %s' % SERVICES +
                         '\n\ncli services: %s' % cli_services)
        for service in SERVICES:
            service_found = False
            for item in cli_services:
                if service == item['Service']:
                    service_found = True
                    break
            self.assertTrue(service_found,
                            '\n\nexpected service %s, ' % service +
                            'not found in ' +
                            '\n\ncli_services: %s' % cli_services)

        """$ kollacli service listgroups

        +------------------------+-------------------------+-----------+
        | Service                | Groups                  | Inherited |
        +------------------------+-------------------------+-----------+
        | cinder                 | ['control', 'control2'] | -         |
        | cinder-api             |                         | yes       |
        | cinder-backup          | ['storage']             | no        |
        | cinder-scheduler       |                         | yes       |
        | cinder-volume          | ['storage']             | no        |
        | glance                 | ['control', 'control2'] | -         |
        | glance-api             |                         | yes       |
        | glance-registry        |                         | yes       |
        ...

        """
        msg = self.run_cli_cmd('service listgroups -f json')
        cli_services = json.loads(msg)

        expect_num_svcs = len(SERVICES)
        for service in SERVICES:
            expect_num_svcs = expect_num_svcs + len(SERVICES[service])
        self.assertEqual(expect_num_svcs, len(cli_services),
                         '# of cli services (%s) ' % len(cli_services) +
                         '!= expected services (%s).' % expect_num_svcs +
                         '\n\nexpected services: %s' % SERVICES +

                         '\n\ncli services: %s' % cli_services)
        for svc in cli_services:
            # get cli info
            cli_service = svc['Service']
            cli_groups = svc['Groups']
            cli_inherited = svc['Inherited']

            if cli_service in DEFAULT_GROUPS:
                # service, not sub-service

                # check default group
                expected_groups = [DEFAULT_GROUPS[cli_service]]
                self.assertEqual(expected_groups, cli_groups)

                # inherited should be '-' for services
                self.assertEqual('-', cli_inherited,
                                 'cli_inherited (%s) ' % cli_inherited +
                                 'for service (%s) ' % cli_service +
                                 'is not "-"')
            else:
                # sub-service

                # check default groups
                if cli_service in DEFAULT_OVERRIDES:

                    # service is overriden, inherited = no
                    self.assertEqual('no', cli_inherited,
                                     'cli_inherited (%s) ' % cli_inherited +
                                     'for overriden sub-service (%s), '
                                     % cli_service +
                                     'is not "no"')
                    # check groups
                    expected_groups = [DEFAULT_OVERRIDES[cli_service]]
                    self.assertEqual(expected_groups, cli_groups,
                                     'sub-service (%s), ' % cli_service +
                                     'expected groups: %s, '
                                     % expected_groups +
                                     'cli_groups: %s' % cli_groups)

                else:
                    # service is not overriden, inherited = yes
                    self.assertEqual('yes', cli_inherited,
                                     'cli_inherited (%s) ' % cli_inherited +
                                     'for overriden sub-service (%s), '
                                     % cli_service +
                                     'is not "yes"')
                    # overriden means no groups
                    self.assertEqual('', cli_groups,
                                     'sub-service (%s), ' % cli_service +
                                     'expected groups: "", '
                                     'cli_groups: %s' % cli_groups)

    def test_service_add_group(self):

        service = 'cinder'
        new_group = 'network'

        # add new group to a service
        self.run_cli_cmd('service addgroup %s %s' % (service, new_group))

        msg = self.run_cli_cmd('service listgroups -f json')
        cli_services = json.loads(msg)
        cli_service = ''
        for svc in cli_services:
            if svc['Service'] == service:
                cli_service = svc
                break
        self.assertNotEqual(cli_service, '',
                            'service: %s, ' % service +
                            'not found in cli_services: \n%s'
                            % cli_service)
        cli_groups = cli_service['Groups']
        expected_groups = [DEFAULT_GROUPS[service], '%s' % new_group]
        self.assertEqual(expected_groups, cli_groups,
                         'service: %s, ' % service +
                         'expected groups: %s, ' % expected_groups +
                         'cli_groups: %s' % cli_groups)

        # remove that group
        self.run_cli_cmd('service removegroup %s %s' % (service, new_group))

        msg = self.run_cli_cmd('service listgroups -f json')
        cli_services = json.loads(msg)
        for svc in cli_services:
            if svc['Service'] == service:
                cli_service = svc
                break
        self.assertNotEqual(cli_service, '',
                            'service: %s, ' % service +
                            'not found in cli_services: \n%s'
                            % cli_service)
        cli_groups = cli_service['Groups']
        expected_groups = [DEFAULT_GROUPS[service]]
        self.assertEqual(expected_groups, cli_groups,
                         'service: %s, ' % service +
                         'expected groups: %s, ' % expected_groups +
                         'cli_groups: %s' % cli_groups)

        service = 'glance-api'
        new_group = 'compute'

        # add new group to a sub-service
        self.run_cli_cmd('service addgroup %s %s' % (service, new_group))

        msg = self.run_cli_cmd('service listgroups -f json')
        cli_services = json.loads(msg)
        for svc in cli_services:
            if svc['Service'] == service:
                cli_service = svc
                break
        self.assertNotEqual(cli_service, '',
                            'service: %s, ' % service +
                            'not found in cli_services: \n%s'
                            % cli_service)
        cli_groups = cli_service['Groups']
        cli_inherited = cli_service['Inherited']
        expected_groups = ['%s' % new_group]
        self.assertEqual(expected_groups, cli_groups,
                         'service: %s, ' % service +
                         'expected groups: %s, ' % expected_groups +
                         'cli_groups: %s' % cli_groups)

        self.assertEqual('no', cli_inherited,
                         'cli_inherited (%s) ' % cli_inherited +
                         'for overriden sub-service (%s), '
                         % service +
                         'is not "no"')

        # remove that group
        self.run_cli_cmd('service removegroup %s %s' % (service, new_group))

        msg = self.run_cli_cmd('service listgroups -f json')
        cli_services = json.loads(msg)
        for svc in cli_services:
            if svc['Service'] == service:
                cli_service = svc
                break
        self.assertNotEqual(cli_service, '',
                            'service: %s, ' % service +
                            'not found in cli_services: \n%s'
                            % cli_service)
        cli_groups = cli_service['Groups']
        cli_inherited = cli_service['Inherited']
        expected_groups = ''
        self.assertEqual(expected_groups, cli_groups,
                         'service: %s, ' % service +
                         'expected groups: %s, ' % expected_groups +
                         'cli_groups: %s' % cli_groups)
        self.assertEqual('yes', cli_inherited,
                         'cli_inherited (%s) ' % cli_inherited +
                         'for overriden sub-service (%s), '
                         % service +
                         'is not "yes"')


if __name__ == '__main__':
    unittest.main()
