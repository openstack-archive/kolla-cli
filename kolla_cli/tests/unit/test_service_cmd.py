# Copyright (c) 2018 OpenStack Foundation
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from unittest import mock

from kolla_cli.tests.unit.common import KollaCliUnitTest


class TestUnit(KollaCliUnitTest):

    @mock.patch('cliff.lister.Lister.produce_output')
    @mock.patch('kolla_cli.api.client.ClientApi.service_get_all')
    @mock.patch('kolla_cli.shell.KollaCli._is_inventory_present',
                return_value=True)
    def test_service_list(self, _, mock_service_get_all, mock_cliff):
        # list all services, check that output is sorted properly
        servicename1 = 'service1'
        servicename2 = 'service2'
        childnames = ['child2', 'child1']
        fake_service1 = self.get_fake_service(servicename1,
                                              childnames=childnames)
        fake_service2 = self.get_fake_service(servicename2,
                                              childnames=childnames)
        mock_service_get_all.return_value = [fake_service2, fake_service1]
        ret = self.run_cli_command('service list')
        self.assertEqual(ret, 0)
        mock_service_get_all.assert_called_once_with()

        expected_childnames = '[child1,child2]'
        mock_cliff.assert_called_once_with(
            mock.ANY, ('Service', 'Children'),
            [(servicename1, expected_childnames),
             (servicename2, expected_childnames)
             ])

    @mock.patch('kolla_cli.api.client.ClientApi.service_get_all')
    @mock.patch('kolla_cli.shell.KollaCli._is_inventory_present',
                return_value=True)
    def test_service_grouplist(self, _, mock_service_get_all):
        # list all services with their groups
        servicename = 'service1'
        groupname = 'group1'
        fake_service = self.get_fake_service(servicename,
                                             groupnames=[groupname])
        mock_service_get_all.return_value = [fake_service]
        ret = self.run_cli_command('service listgroups')
        self.assertEqual(ret, 0)
        mock_service_get_all.assert_called_once_with()

    @mock.patch('kolla_cli.api.group.Group.add_service')
    @mock.patch('kolla_cli.api.client.ClientApi.group_get')
    @mock.patch('kolla_cli.shell.KollaCli._is_inventory_present',
                return_value=True)
    def test_service_addgroup(self, _, mock_group_get,
                              mock_group_add_service):
        servicename = 'service1'
        groupname = 'group1'
        fake_group = self.get_fake_group(groupname)
        mock_group_get.return_value = [fake_group]
        ret = self.run_cli_command('service addgroup %s %s'
                                   % (servicename, groupname))
        self.assertEqual(ret, 0)
        mock_group_get.assert_called_once_with([groupname])
        mock_group_add_service.assert_called_once_with(servicename)

    @mock.patch('kolla_cli.api.group.Group.remove_service')
    @mock.patch('kolla_cli.api.client.ClientApi.group_get')
    @mock.patch('kolla_cli.shell.KollaCli._is_inventory_present',
                return_value=True)
    def test_service_removegroup(self, _, mock_group_get,
                                 mock_group_remove_service):
        servicename = 'service1'
        groupname = 'group1'
        fake_group = self.get_fake_group(groupname,
                                         servicenames=[servicename])
        mock_group_get.return_value = [fake_group]
        ret = self.run_cli_command('service removegroup %s %s'
                                   % (servicename, groupname))
        self.assertEqual(ret, 0)
        mock_group_get.assert_called_once_with([groupname])
        mock_group_remove_service.assert_called_once_with(servicename)
