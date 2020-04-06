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
    @mock.patch('kolla_cli.api.client.ClientApi.group_add')
    @mock.patch('kolla_cli.shell.KollaCli._is_inventory_present',
                return_value=True)
    def test_group_add(self, _, mock_add):
        groupname = 'group1'
        ret = self.run_cli_command('group add %s' % groupname)
        self.assertEqual(ret, 0)
        mock_add.assert_called_once_with([groupname])

    @mock.patch('kolla_cli.api.client.ClientApi.group_remove')
    @mock.patch('kolla_cli.shell.KollaCli._is_inventory_present',
                return_value=True)
    def test_group_remove(self, _, mock_remove):
        groupname = 'group1'
        ret = self.run_cli_command('group remove %s' % groupname)
        self.assertEqual(ret, 0)
        mock_remove.assert_called_once_with([groupname])

    @mock.patch('kolla_cli.api.client.ClientApi.group_get_all')
    @mock.patch('kolla_cli.shell.KollaCli._is_inventory_present',
                return_value=True)
    def test_group_listhosts(self, _, mock_group_get_all):
        # list all groups and their hosts
        hostname = 'foo'
        groupname = 'group1'
        fake_group = self.get_fake_group(groupname, hostnames=[hostname])
        mock_group_get_all.return_value = [fake_group]
        ret = self.run_cli_command('group listhosts')
        self.assertEqual(ret, 0)
        mock_group_get_all.assert_called_once_with()

    @mock.patch('kolla_cli.api.group.Group.add_host')
    @mock.patch('kolla_cli.api.client.ClientApi.group_get')
    @mock.patch('kolla_cli.shell.KollaCli._is_inventory_present',
                return_value=True)
    def test_group_addhost(self, _, mock_group_get, mock_group_add_host):
        hostname = 'foo'
        groupname = 'group1'
        fake_group = self.get_fake_group(groupname)
        mock_group_get.return_value = [fake_group]
        ret = self.run_cli_command('group addhost %s %s'
                                   % (groupname, hostname))
        self.assertEqual(ret, 0)
        mock_group_get.assert_called_once_with([groupname])
        mock_group_add_host.assert_called_once_with(hostname)

    @mock.patch('kolla_cli.api.group.Group.remove_host')
    @mock.patch('kolla_cli.api.client.ClientApi.group_get')
    @mock.patch('kolla_cli.shell.KollaCli._is_inventory_present',
                return_value=True)
    def test_group_removehost(self, _, mock_group_get,
                              mock_group_remove_host):
        hostname = 'foo'
        groupname = 'group1'
        fake_group = self.get_fake_group(groupname, hostnames=[hostname])
        mock_group_get.return_value = [fake_group]
        ret = self.run_cli_command('group removehost %s %s'
                                   % (groupname, hostname))
        self.assertEqual(ret, 0)
        mock_group_get.assert_called_once_with([groupname])
        mock_group_remove_host.assert_called_once_with(hostname)

    @mock.patch('kolla_cli.api.client.ClientApi.group_get_all')
    @mock.patch('kolla_cli.shell.KollaCli._is_inventory_present',
                return_value=True)
    def test_group_listservices(self, _, mock_group_get_all):
        # list all groups and their services
        servicename = 'service1'
        groupname = 'group1'
        fake_group = self.get_fake_group(groupname,
                                         servicenames=[servicename])
        mock_group_get_all.return_value = [fake_group]
        ret = self.run_cli_command('group listservices')
        self.assertEqual(ret, 0)
        mock_group_get_all.assert_called_once_with()
