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
from common import KollaCliTest

import json
import unittest

from kollacli.common.allinone import AllInOne
from kollacli.common.inventory import Inventory


class TestFunctional(KollaCliTest):

    def test_service_list(self):
        """$ kollacli service list -f json

        [{"Service": "aodh", "Sub-Services": ["aodh-api", "aodh-evaluator",
        "aodh-notifier", "aodh-listener"]}, {"Service": "ceilometer",
        "Sub-Services": ["ceilometer-api", "ceilometer-central",
        "ceilometer-collector", "ceilometer-compute",
        "ceilometer-notification"]}...]
        """
        def _check_service(service, cli_service):
            subservicenames = service.get_sub_servicenames()
            cli_subservices = cli_service['Sub-Services']
            self.assertEqual(len(subservicenames), len(cli_subservices),
                             ('cli has different # of sub services. ',
                              'cli: %s, ' % cli_subservices,
                              'allineone: %s' % subservicenames))
            for sub_servicename in subservicenames:
                sub_found = False
                for cli_subservice in cli_subservices:
                    if cli_subservice == sub_servicename:
                        sub_found = True
                        break
                self.assertIs(True, sub_found, 'cli subservice %s not found'
                              % cli_subservice)

        msg = self.run_cli_cmd('service list -f json')
        cli_services = json.loads(msg)
        allinone = AllInOne()
        num_services = len(allinone.services.keys())
        self.assertEqual(num_services, len(cli_services),
                         '# of cli services != expected services.' +
                         '\n\nexpected services: %s'
                         % allinone.services.keys() +
                         '\n\ncli services: %s' % cli_services)

        for servicename, service in allinone.services.items():
            service_found = False
            for cli_service in cli_services:
                if cli_service['Service'] == servicename:
                    service_found = True
                    _check_service(service, cli_service)
            self.assertTrue(service_found,
                            '\n\nexpected service %s, ' % servicename +
                            'not found in ' +
                            '\n\ncli_services: %s' % cli_services)

    def test_listgroups(self):
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

        allinone = AllInOne()
        num_services = len(allinone.services.keys())
        num_subservices = len(allinone.sub_services.keys())
        num_all = num_services + num_subservices
        self.assertEqual(num_all, len(cli_services),
                         '# of cli services (%s) ' % len(cli_services) +
                         '!= # of expected services (%s).' % num_all +
                         '\n\ncli services: %s' % cli_services)

        for svc in cli_services:
            # get cli info
            cli_service = svc['Service']
            cli_groups = svc['Groups']
            cli_inherited = svc['Inherited']

            if '-' not in cli_service:
                # service, not sub-service

                # check default group
                expected_groups = \
                    allinone.services[cli_service].get_groupnames()
                self.assertEqual(expected_groups, cli_groups)

                # inherited should be '-' for services
                self.assertEqual('-', cli_inherited,
                                 'cli_inherited (%s) ' % cli_inherited +
                                 'for service (%s) ' % cli_service +
                                 'is not "-"')
            else:
                # sub-service
                sub_service = allinone.sub_services[cli_service]

                # check default groups
                groupnames = sub_service.get_groupnames()
                if groupnames:

                    # service is overriden, inherited = no
                    self.assertEqual('no', cli_inherited,
                                     'cli_inherited (%s) ' % cli_inherited +
                                     'for overriden sub-service (%s), '
                                     % cli_service +
                                     'is not "no"')
                    # check groups
                    expected_groups = groupnames
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

        servicename = 'glance-api'
        new_group = 'compute'

        # add new group to a sub-service
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
        cli_inherited = cli_service['Inherited']
        expected_groups = ''
        self.assertEqual(expected_groups, cli_groups,
                         'service: %s, ' % servicename +
                         'expected groups: %s, ' % expected_groups +
                         'cli_groups: %s' % cli_groups)
        self.assertEqual('yes', cli_inherited,
                         'cli_inherited (%s) ' % cli_inherited +
                         'for overriden sub-service (%s), '
                         % service +
                         'is not "yes"')

        test_group = 'testgroup'
        self.run_cli_cmd('group add %s' % test_group)
        self.run_cli_cmd('service addgroup cinder %s' % test_group)
        self.run_cli_cmd('group remove %s' % test_group)
        msg = self.run_cli_cmd('service listgroups -f json')
        self.assertNotIn(test_group, msg,
                         'Group: %s, still listed in services: %s'
                         % (test_group, msg))

    def test_ceph(self):
        # ceph has an odd structure in the upstream all-in-one file.
        # It was changed in 3.0.1 of kolla. This test is to check that
        # the kolla change was not overwritten by a kolla update from upstream.
        # If the upstream file is used, ceph will default to having no
        # groups.
        inventory = Inventory.load()
        ceph = inventory.get_service('ceph')
        groups = ceph.get_groupnames()
        self.assertIsNot(groups, 'ceph has no groups, could be due to '
                         'using an unpatched upstream all-in-one file.')


if __name__ == '__main__':
    unittest.main()
