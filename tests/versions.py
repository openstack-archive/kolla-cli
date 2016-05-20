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

from kollacli.api.client import ClientApi

import os
import unittest

CLIENT = ClientApi()

PKG_VERSION_TAG = '%global package_version'
SETUP_VERSION_TAG = 'version ='

RPM_SPEC_PATH = 'buildrpm/openstack-kollacli.spec'
SETUP_PATH = 'setup.cfg'


class TestFunctional(KollaCliTest):

    def test_versions(self):
        """test versions

        cli versions are located in these files:
        - setup.cfg
        - buildrpm/openstack-kollacli.spec

        This will verify that they all match what is in the rpm spec.

        This test only runs if the cwd is either the root dev directory or the
        tools directory. This should work in both tox and eclipse environments.
        """
        cwd = os.getcwd()
        prefix = None
        if os.path.exists(os.path.join(cwd, RPM_SPEC_PATH)):
            prefix = ''
        elif os.path.exists(os.path.join(cwd, '../' + RPM_SPEC_PATH)):
            prefix = '../'
        if prefix is None:
            # skip test, can't find rpm spec file
            self.log.info('No rpm spec file found. cwd is %s. ' % cwd,
                          'Skipping test.')
            return

        pkg_version = self._get_version_from_file(prefix + RPM_SPEC_PATH,
                                                  PKG_VERSION_TAG)
        setup_version = self._get_version_from_file(prefix + SETUP_PATH,
                                                    SETUP_VERSION_TAG)
        self.assertEqual(pkg_version, setup_version,
                         'rpm_spec vs setup.cfg mis-match')

        # check that the client version is readble
        version = CLIENT.get_version()
        self.assertIsNotNone(version, 'version is None')

    def _get_version_from_file(self, path, tag):
        version = None
        with open(path, 'r') as vfile:
            for line in vfile:
                if line.startswith(tag):
                    version = line.split(tag)[1]
                    version = version.strip()
                    version = version.replace("'", "")
                    break
        self.assertIsNotNone(version,
                             'version tag: [%s], not found in file: %s'
                             % (tag, path))
        return version


if __name__ == '__main__':
    unittest.main()
