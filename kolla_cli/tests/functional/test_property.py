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
import os
import unittest

from kolla_cli.common.utils import get_group_vars_dir
from kolla_cli.common.utils import get_host_vars_dir
from kolla_cli.common.utils import get_kolla_ansible_home

from kolla_cli.common.inventory import Inventory


class TestFunctional(KollaCliTest):

    def test_properties(self):
        # test global properties
        self._properties_test()

        # test single group vars
        group = 'prop_test_group1'
        self.run_cli_cmd('group add %s' % group)
        self._properties_test(groups=['control'])

        # test single host vars
        host = 'prop_test_host1'
        self.run_cli_cmd('host add %s' % host)
        self._properties_test(hosts=[host])

        # test multiple group vars
        groups = [group]
        group = 'prop_test_group2'
        groups.append(group)
        self.run_cli_cmd('group add %s' % group)
        self._properties_test(groups=groups)

        # test multiple host vars
        hosts = [host]
        host = 'prop_test_host2'
        hosts.append(host)
        self.run_cli_cmd('host add %s' % host)
        self._properties_test(hosts=hosts)

        # test all group vars
        self._properties_test(groups=['all'])

        # test all host vars
        self._properties_test(hosts=['all'])

        # test property override output
        ovr_key = 'enable_haproxy'
        ovr_value = 'no'

        # clear property values before test
        self.run_cli_cmd('property clear %s' % ovr_key)
        self.run_cli_cmd('property clear %s --host=all' % ovr_key)
        self.run_cli_cmd('property clear %s --group=all' % ovr_key)

        # global property override test
        self.run_cli_cmd('property set %s %s' % (ovr_key, ovr_value))
        json_str = self.run_cli_cmd('property list -f json')
        msg = self._override_test(json_str, ovr_key, ovr_value, '*--')
        self.assertEqual(msg, '', 'override check failed: %s' % msg)

        # host property override test
        self.run_cli_cmd('property set %s %s --host=%s' %
                         (ovr_key, ovr_value, host))
        json_str = self.run_cli_cmd('property list -f json --host=%s' % host)
        msg = self._override_test(json_str, ovr_key,
                                  ovr_value, '*-H', host=host)
        self.assertEqual(msg, '', 'host override check failed: %s' % msg)

        # group property override test
        self.run_cli_cmd('property set %s %s --group=%s' %
                         (ovr_key, ovr_value, group))
        json_str = self.run_cli_cmd('property list -f json --group=%s' % group)
        msg = self._override_test(json_str, ovr_key,
                                  ovr_value, '*GH', group=group)
        self.assertEqual(msg, '', 'group override check failed: %s' % msg)

        # check that group_var files are deleted
        # when groups are deleted
        for group in groups:
            path = os.path.join(get_group_vars_dir(), group)
            self.assertTrue(os.path.exists(path))
            self.run_cli_cmd('group remove %s' % group)
            self.assertFalse(os.path.exists(path))

        # check that host_var files are deleted
        # when hosts are deleted
        for host in hosts:
            path = os.path.join(get_host_vars_dir(), host)
            self.assertTrue(os.path.exists(path))
            self.run_cli_cmd('host remove %s' % host)
            self.assertFalse(os.path.exists(path))

    def _properties_test(self, groups=[], hosts=[]):
        switch = ''
        if groups:
            switch = '--groups'
            dir_name = 'group_vars'
        elif hosts:
            switch = '--hosts'
            dir_name = 'host_vars'

        key = 'TeStKeY'
        value = 'TeStVaLuE:123:abc'

        # initialize keys
        targets_csv = ''
        targets = groups + hosts
        if 'all' in groups:
            inv = Inventory.load()
            targets = inv.get_groupnames()
            targets_csv = 'all'
        elif 'all' in hosts:
            inv = Inventory.load()
            targets = inv.get_hostnames()
            targets_csv = 'all'

        comma = ''
        sizes = {}  # key = path, value = [size1, size2, etc]
        for target in targets:
            self.run_cli_cmd('property clear %s %s %s'
                             % (switch, target, key))
            if targets_csv != 'all':
                targets_csv += comma + target
                comma = ','
            path = os.path.join(get_kolla_ansible_home(),
                                'ansible', dir_name, target)
            sizes[path] = [os.path.getsize(path)]
        if not switch:
            self.run_cli_cmd('property clear %s' % key)
            path = os.path.join(get_kolla_ansible_home(),
                                'ansible/group_vars/__GLOBAL__')
            sizes[path] = [os.path.getsize(path)]

        # test append
        self.run_cli_cmd('property set %s %s %s %s'
                         % (switch, targets_csv, key, value))
        if switch:
            msg = self.run_cli_cmd('property list -f json %s all'
                                   % (switch))
        else:
            msg = self.run_cli_cmd('property list -f json')
        err_msg = self._check_property_values(key, value, msg, targets)
        self.assertEqual(err_msg, '',
                         'set failed property not in output: %s, %s (%s %s)'
                         % (key, value, switch, targets_csv))

        bad_path = self._is_size_ok(sizes, 0, '<', 1)
        self.assertIsNone(bad_path, 'Size of file %s did not ' % bad_path +
                          'increase after append (%s %s)'
                          % (switch, targets_csv))

        # test modify existing
        value += '2'
        self.run_cli_cmd('property set %s %s %s %s'
                         % (switch, targets_csv, key, value))
        msg = self.run_cli_cmd('property list --all -f json %s %s'
                               % (switch, targets_csv))
        err_msg = self._check_property_values(key, value, msg, targets)
        self.assertEqual(err_msg, '',
                         'set failed property not in output: %s, %s (%s %s)'
                         % (key, value, switch, targets_csv))
        bad_path = self._is_size_ok(sizes, 1, '<', 2)
        self.assertIsNone(bad_path, 'Size of file %s did not ' % bad_path +
                          'increase after modify (%s %s)'
                          % (switch, targets_csv))

        # test clear
        self.run_cli_cmd('property clear %s %s %s'
                         % (switch, targets_csv, key))
        msg = self.run_cli_cmd('property list --long -f json %s %s'
                               % (switch, targets_csv))
        err_msg = self._check_property_values(key, value, msg, targets)
        self.assertTrue('missing' in err_msg,
                        'clear failed, property still in output: ' +
                        '%s, %s (%s %s)'
                        % (key, value, switch, targets_csv))
        bad_path = self._is_size_ok(sizes, 0, '=', 3)
        self.assertIsNone(bad_path, 'Size of file %s is ' % bad_path +
                          'different from initial size '
                          '(%s %s %s)'
                          % (switch, targets_csv, str(sizes)))

        # test setting empty string
        value = '""'
        self.run_cli_cmd('property set %s %s %s %s'
                         % (switch, targets_csv, key, value))
        msg = self.run_cli_cmd('property list --all -f json %s %s'
                               % (switch, targets_csv))
        err_msg = self._check_property_values(key, value, msg, targets)
        self.assertTrue('missing' in err_msg,
                        'clear failed, property still in output: ' +
                        '%s, %s (%s %s)'
                        % (key, value, switch, targets_csv))
        self.run_cli_cmd('property clear %s %s %s'
                         % (switch, targets_csv, key))

    def _check_property_values(self, key, value, json_str,
                               targets=[]):
        """Verify cli data against model data"""
        error_msg = ''
        props = json.loads(json_str.strip())
        if not targets:
            # simple property check
            ok = False
            for prop in props:
                if (prop['Property Name'] == key and
                        prop['Property Value'] == value):
                    ok = True
            if not ok:
                error_msg = '%s:%s is missing in __GLOBAL__'
        else:
            target_map = {}
            for target in targets:
                target_map[target] = 'missing'
                for prop in props:
                    if 'Group' in prop and prop['Group'] == target:
                        if (prop['Property Name'] == key and
                                prop['Property Value'] == value):
                            target_map[target] = 'ok'
                    elif 'Host' in prop and prop['Host'] == target:
                        if (prop['Property Name'] == key and
                                prop['Property Value'] == value):
                            target_map[target] = 'ok'
            for target, state in target_map.items():
                if state == 'missing':
                    error_msg += ('%s:%s is missing in %s\n output:%s\n'
                                  % (key, value, target, json_str))
        return error_msg

    def _is_size_ok(self, sizes, idx0, comparator, idx1):
        bad_path = None
        for path, path_sizes in sizes.items():
            if idx1 > len(path_sizes) - 1:
                # get new sizes
                sizes[path].append(os.path.getsize(path))
            if comparator == '=':
                if sizes[path][idx0] != sizes[path][idx1]:
                    bad_path = path
                    break
            elif comparator == '<':
                if sizes[path][idx0] >= sizes[path][idx1]:
                    bad_path = path
                    break
        return bad_path

    def _override_test(self, json_str, key, value, ovr_string,
                       host=None, group=None):
        error_msg = ''
        props = json.loads(json_str.strip())
        for prop in props:
            if group is not None:
                if prop['Group'] == group:
                    error_msg = self._check_override_value(prop, key,
                                                           value, ovr_string)
            elif host is not None:
                if prop['Host'] == host:
                    error_msg = self._check_override_value(prop, key,
                                                           value, ovr_string)
            else:
                error_msg = self._check_override_value(prop, key,
                                                       value, ovr_string)
        return error_msg

    def _check_override_value(self, prop, key, value, ovr_string):
        error_msg = ''
        if(prop['Property Name'] == key and
           prop['Property Value'] == value and
           prop['OVR'] != ovr_string):
            error_msg = ('override value mismatch for '
                         'key:%s value:%s ovr:%s target:%s' %
                         (key, value, prop['OVR'], ovr_string))
        return error_msg


if __name__ == '__main__':
    unittest.main()
