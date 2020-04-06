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
    @mock.patch('kolla_cli.api.client.ClientApi.host_add')
    @mock.patch('kolla_cli.shell.KollaCli._is_inventory_present',
                return_value=True)
    def test_host_add(self, _, mock_add):
        hostname = 'foo'
        ret = self.run_cli_command('host add %s' % hostname)
        self.assertEqual(ret, 0)
        mock_add.assert_called_once_with([hostname])

    @mock.patch('kolla_cli.api.client.ClientApi.host_remove')
    @mock.patch('kolla_cli.shell.KollaCli._is_inventory_present',
                return_value=True)
    def test_host_remove(self, _, mock_remove):
        hostname = 'foo'
        ret = self.run_cli_command('host remove %s' % hostname)
        self.assertEqual(ret, 0)
        mock_remove.assert_called_once_with([hostname])

    @mock.patch('kolla_cli.api.client.ClientApi.host_get_all')
    @mock.patch('kolla_cli.api.client.ClientApi.host_get')
    @mock.patch('kolla_cli.shell.KollaCli._is_inventory_present',
                return_value=True)
    def test_host_list(self, _, mock_get, mock_get_all):
        # get all hosts
        mock_get_all.return_value = []
        ret = self.run_cli_command('host list')
        self.assertEqual(ret, 0)
        mock_get_all.assert_called_once_with()

        # get a specific host
        hostname = 'foo'
        mock_get.return_value = []
        ret = self.run_cli_command('host list %s' % hostname)
        self.assertEqual(ret, 0)
        mock_get.assert_called_once_with([hostname])

    @mock.patch('kolla_cli.commands.host.HostDestroy._is_ok_to_delete_data',
                return_value='y')
    @mock.patch('kolla_cli.common.ansible.job.AnsibleJob.get_status')
    @mock.patch('kolla_cli.api.client.ClientApi.host_get_all')
    @mock.patch('kolla_cli.api.client.ClientApi.host_destroy')
    @mock.patch('kolla_cli.shell.KollaCli._is_inventory_present',
                return_value=True)
    def test_host_destroy(self, _, mock_destroy, mock_get_all,
                          mock_get_status, mock_prompt):
        hostname = 'foo'
        mock_get_all.return_value = [self.get_fake_host(hostname)]
        mock_destroy.return_value = self.get_fake_job()
        mock_get_status.return_value = 0

        # default destroy hostname
        ret = self.run_cli_command('host destroy %s' % hostname)
        self.assertEqual(ret, 0)
        mock_destroy.assert_called_once_with([hostname], 'kill', 1,
                                             False, False)
        # destroy all
        mock_destroy.reset_mock()
        ret = self.run_cli_command('host destroy all')
        self.assertEqual(ret, 0)
        mock_destroy.assert_called_once_with([hostname], 'kill', 1,
                                             False, False)
        # destroy --stop
        mock_destroy.reset_mock()
        ret = self.run_cli_command('host destroy %s --stop' % hostname)
        self.assertEqual(ret, 0)
        mock_destroy.assert_called_once_with([hostname], 'stop', 1,
                                             False, False)
        # destroy --includedata
        mock_destroy.reset_mock()
        ret = self.run_cli_command('host destroy %s --includedata' % hostname)
        self.assertEqual(ret, 0)
        mock_destroy.assert_called_once_with([hostname], 'kill', 1,
                                             True, False)

        # destroy --removeimages
        mock_destroy.reset_mock()
        ret = self.run_cli_command('host destroy %s --removeimages'
                                   % hostname)
        self.assertEqual(ret, 0)
        mock_destroy.assert_called_once_with([hostname], 'kill', 1,
                                             False, True)

    @mock.patch('kolla_cli.commands.host.LOG.info')
    @mock.patch('kolla_cli.api.client.ClientApi.host_get_all')
    @mock.patch('kolla_cli.api.client.ClientApi.host_ssh_check')
    @mock.patch('kolla_cli.shell.KollaCli._is_inventory_present',
                return_value=True)
    def test_host_ssh_check(self, _, mock_ssh_check, mock_get_all, mock_log):
        hostname = 'foo'
        check_ok_response = {hostname: {'success': True}}
        check_bad_response = {hostname: {'success': False, 'msg': 'FAILED'}}
        mock_get_all.return_value = [self.get_fake_host(hostname)]

        # host check hostname (success)
        mock_ssh_check.return_value = check_ok_response
        ret = self.run_cli_command('host check %s' % hostname)
        self.assertEqual(ret, 0)
        mock_ssh_check.assert_called_once_with([hostname])
        mock_log.assert_called_once_with('Host %s: success ' % hostname)

        # host check all (success)
        mock_ssh_check.reset_mock()
        mock_log.reset_mock()
        mock_ssh_check.return_value = check_ok_response
        ret = self.run_cli_command('host check all')
        self.assertEqual(ret, 0)
        mock_ssh_check.assert_called_once_with([hostname])
        mock_log.assert_called_once_with('Host %s: success ' % hostname)

        # host check hostname (fail)
        mock_ssh_check.reset_mock()
        mock_log.reset_mock()
        mock_ssh_check.return_value = check_bad_response
        ret = self.run_cli_command('host check %s' % hostname)
        self.assertEqual(ret, 1)
        mock_ssh_check.assert_called_once_with([hostname])
        mock_log.assert_called_once_with('Host %s: failed- FAILED' % hostname)

    @mock.patch('kolla_cli.commands.host.HostSetup._get_yml_data')
    @mock.patch('getpass.getpass')
    @mock.patch('kolla_cli.commands.host.ClientApi.host_ssh_check')
    @mock.patch('kolla_cli.commands.host.ClientApi.host_setup')
    @mock.patch('kolla_cli.api.client.ClientApi.host_get_all')
    @mock.patch('kolla_cli.shell.KollaCli._is_inventory_present',
                return_value=True)
    def test_host_setup(self, _, mock_get_all, mock_setup, mock_ssh_check,
                        mock_passwd, mock_yml):
        password = 'PASSWORD'
        hostname = 'foo'
        mock_get_all.return_value = [self.get_fake_host(hostname)]
        mock_passwd.return_value = password

        # single host setup (host not yet setup)
        mock_ssh_check.return_value = {hostname: {'success': False}}
        ret = self.run_cli_command('host setup %s' % hostname)
        self.assertEqual(ret, 0)
        mock_ssh_check.assert_called_once_with([hostname])
        mock_setup.assert_called_once_with({hostname: {'password': password}})

        # single host setup --insecure (host already setup)
        mock_ssh_check.reset_mock()
        mock_setup.reset_mock()
        mock_ssh_check.return_value = {hostname: {'success': True}}
        ret = self.run_cli_command('host setup %s --insecure %s'
                                   % (hostname, password))
        self.assertEqual(ret, 0)
        mock_ssh_check.assert_called_once_with([hostname])
        mock_setup.assert_not_called()

        # multi-host setup
        mock_ssh_check.reset_mock()
        mock_setup.reset_mock()
        fake_path = '/bogus'
        mock_yml.return_value = {hostname: {'password': password}}
        ret = self.run_cli_command('host setup --file %s' % fake_path)
        self.assertEqual(ret, 0)
        mock_setup.assert_called_once_with({hostname: {'password': password}})
        mock_yml.assert_called_once_with(fake_path)
        mock_ssh_check.assert_not_called()
