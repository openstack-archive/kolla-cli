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
    @mock.patch('kolla_cli.api.control_plane.ControlPlaneApi.deploy')
    @mock.patch('kolla_cli.common.ansible.job.AnsibleJob.get_status')
    @mock.patch('kolla_cli.shell.KollaCli._is_inventory_present',
                return_value=True)
    def test_deploy(self, _, mock_get_status, mock_deploy):
        mock_get_status.return_value = 0
        mock_deploy.return_value = self.get_fake_job()
        ret = self.run_cli_command('action deploy')
        self.assertEqual(ret, 0)
        mock_deploy.assert_called_once_with(None, False, 1, None)

    @mock.patch('kolla_cli.api.control_plane.ControlPlaneApi.deploy')
    @mock.patch('kolla_cli.common.ansible.job.AnsibleJob.get_status')
    @mock.patch('kolla_cli.shell.KollaCli._is_inventory_present',
                return_value=True)
    def test_deploy_with_services(self, _, mock_get_status, mock_deploy):
        mock_get_status.return_value = 0
        mock_deploy.return_value = self.get_fake_job()
        services = ['foo', 'bar']
        ret = self.run_cli_command(
            'action deploy --services {}'.format(','.join(services)))
        self.assertEqual(ret, 0)
        mock_deploy.assert_called_once_with(None, False, 1, services)
