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

import logging
import os
import shutil
import unittest

from kolla_cli.api.client import ClientApi
from kolla_cli.common.ansible_inventory import AnsibleInventory
from kolla_cli.common.utils import get_kolla_cli_etc

INV_NAME = 'inventory.json'

CLIENT = ClientApi()
LOG = logging.getLogger(__name__)


class TestFunctional(KollaCliTest):
    """Test description

    This test will look for old version inventory files in the local current
    working directory. If none are found, it will look in the user's home
    directory. If none are found there too, it will print a warning and skip
    the test.

    Old version inventory files must be named inventory.json.v1,
    inventory.json.v2, etc.

    An upgrade test will be run on each old version inventory file that is
    found.
    """
    def test_upgrade(self):
        inv_fpaths = self._find_inv_fpaths()
        if not inv_fpaths:
            LOG.warning('No old version inventory files were found. '
                        'Skipping test.')
        for inv_fpath in inv_fpaths:
            version = self._get_version(inv_fpath)
            self._replace_inventory(inv_fpath)
            self._test_upgrade(version)

    def _get_version(self, inv_fpath):
        try:
            version = int(inv_fpath.split('.v')[1])
        except Exception:
            raise Exception('Invalid version number on old inventory file: %s'
                            % inv_fpath)
        return version

    def _find_inv_fpaths(self):
        """find old version inventories

        Look in order at these locations:
        - current working directory
        - home directory
        """
        fpaths = []
        search_dirs = [os.getcwd(), os.path.expanduser('~')]
        for search_dir in search_dirs:
            fpaths = self._get_inv_fpaths(search_dir)
            if fpaths:
                break
        return fpaths

    def _get_inv_fpaths(self, inv_dir):
        upg_inventory_paths = []
        fnames = os.listdir(inv_dir)
        for fname in fnames:
            if fname.startswith(INV_NAME + '.v'):
                path = os.path.join(inv_dir, fname)
                upg_inventory_paths.append(path)
        return upg_inventory_paths

    def _replace_inventory(self, old_version_inv_path):
        inv_path = os.path.join(get_kolla_cli_etc(),
                                'ansible', 'inventory.json')
        shutil.copyfile(old_version_inv_path, inv_path)

    def _test_upgrade(self, version):
        hostname = 'test_host_upg'

        # This host add will cause the inventory to be upgraded
        CLIENT.host_add([hostname])
        CLIENT.host_remove([hostname])

        # run tests for each version:
        if version <= 1:
            self._test_v1_upgrade()

        if version <= 2:
            self._test_v2_upgrade()

    def _test_v1_upgrade(self):
        # this is a v1 inventory
        # in v1 > v2, ceilometer was added, check that it's there
        # and verify that all ceilometer groups are in the same groups
        # as heat.
        ansible_inventory = AnsibleInventory()
        heat = CLIENT.service_get(['heat'])[0]
        expected_groups = sorted(heat.get_groups())
        ceilometer = ansible_inventory.services['ceilometer']
        expected_services = ceilometer.get_sub_servicenames()
        expected_services.append('ceilometer')
        expected_services = sorted(expected_services)
        services = CLIENT.service_get_all()
        services_found = []

        for service in services:
            servicename = service.get_name()
            if servicename.startswith('ceilometer'):
                groups = sorted(service.get_groups())
                if servicename == 'ceilometer':
                    self.assertEqual(expected_groups, groups,
                                     'groups mismatch between '
                                     'ceilometer '
                                     'and %s' % servicename)
                elif servicename == 'ceilometer-compute':
                    self.assertEqual(['compute'], groups,
                                     'groups mismatch between '
                                     'ceilometer-compute '
                                     'and %s' % servicename)
                else:
                    # sub-services should have no groups (they inherit)
                    self.assertEqual([], groups,
                                     '%s has unexpected groups'
                                     % servicename)
                services_found.append(servicename)

        services_found = sorted(services_found)
        self.assertEqual(expected_services, services_found,
                         'ceilometer subservices mismatch')

    def _test_v2_upgrade(self):
        # this is a v2 inventory. In the v2 to v3 upgrade, all subservices were
        # fixed up to have a parent service
        services = CLIENT.service_get_all()
        servicenames = []
        for service in services:
            servicenames.append(service.name)
            if '-' in service.name:
                # this is a subservice
                parent = service.get_parent()
                self.assertIsNotNone(parent,
                                     'subservice: %s, is missing its parent'
                                     % service.name)

        # ceilometer-alarms were removed in kolla v3.0.1,
        # check that they're gone
        self.assertNotIn('ceilometer-alarm-evaluator', servicenames,
                         'ceilometer-alarm-evaluator still exists.')
        self.assertNotIn('ceilometer-alarm-notifier', servicenames,
                         'ceilometer-alarm-notifier still exists.')

        # aodh and ceph were added in 3.0.1
        self.assertIn('aodh', servicenames, 'aodh not in inventory')
        self.assertIn('ceph', servicenames, 'ceph not in inventory')


if __name__ == '__main__':
    unittest.main()
