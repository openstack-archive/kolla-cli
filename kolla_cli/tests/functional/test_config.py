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
import kolla_cli.api.properties
import unittest

from kolla_cli.api.client import ClientApi
from kolla_cli.tests.functional.common import KollaCliTest

CLIENT = ClientApi()


class TestFunctional(KollaCliTest):

    def test_config_reset(self):
        # test global property reset
        # set a property and make sure it was set correctly
        property_dict = {'test': 'test'}
        CLIENT.property_set(property_dict)
        fetched_properties = CLIENT.property_get()
        fetched_dict = self._properties_to_dict(fetched_properties)
        self.assertIs(self._in_dict(property_dict, fetched_dict), True,
                      'property set failed')

        # now clear the config and make sure the property we just
        # set is now gone
        CLIENT.config_reset()
        fetched_properties = CLIENT.property_get()
        fetched_dict = self._properties_to_dict(fetched_properties)
        self.assertIs(self._in_dict(property_dict, fetched_dict), False,
                      'global property reset config failed')

        # test host property reset
        host_list = ['test']
        CLIENT.host_add(host_list)
        CLIENT.property_set(property_dict,
                            kolla_cli.api.properties.HOST_TYPE)
        fetched_properties = CLIENT.property_get(
            kolla_cli.api.properties.HOST_TYPE, host_list)
        fetched_dict = self._properties_to_dict(fetched_properties)
        self.assertIs(self._in_dict(property_dict, fetched_dict), True,
                      'host property set failed')

        CLIENT.config_reset()
        # need to add back in the host 'test' or the property
        # get call will fail after a reset
        CLIENT.host_add(host_list)
        fetched_properties = CLIENT.property_get(
            kolla_cli.api.properties.HOST_TYPE, host_list)
        fetched_dict = self._properties_to_dict(fetched_properties)
        self.assertIs(self._in_dict(property_dict, fetched_dict), False,
                      'host property reset config failed')

        # test group property reset
        group_list = ['control']
        CLIENT.property_set(property_dict,
                            kolla_cli.api.properties.GROUP_TYPE)
        fetched_properties = CLIENT.property_get(
            kolla_cli.api.properties.GROUP_TYPE, group_list)
        fetched_dict = self._properties_to_dict(fetched_properties)
        self.assertIs(self._in_dict(property_dict, fetched_dict), True,
                      'group property set failed')

        CLIENT.config_reset()
        fetched_properties = CLIENT.property_get(
            kolla_cli.api.properties.GROUP_TYPE, group_list)
        fetched_dict = self._properties_to_dict(fetched_properties)
        self.assertIs(self._in_dict(property_dict, fetched_dict), False,
                      'group property reset config failed')

        # test host reset
        # add a host and make sure it was added correctly
        host_list = ['test']
        CLIENT.host_add(host_list)
        fetched_hosts = CLIENT.host_get_all()
        fetched_list = self._hosts_to_list(fetched_hosts)
        self.assertIs(set(host_list).issubset(fetched_list), True,
                      'host set failed')

        # now clear the config and make sure the host we just
        # added is now gone
        CLIENT.config_reset()
        fetched_hosts = CLIENT.host_get_all()
        fetched_list = self._hosts_to_list(fetched_hosts)
        self.assertIs(set(host_list).issubset(fetched_list), False,
                      'inventory reset config failed')

        # need to populate the password file or many other tests will fail
        CLIENT.password_init()

    @staticmethod
    def _properties_to_dict(props):
        property_dict = {}
        for prop in props:
            property_dict[prop.name] = prop.value
        return property_dict

    @staticmethod
    def _hosts_to_list(hosts):
        host_list = []
        for host in hosts:
            host_list.append(host.name)
        return host_list

    @staticmethod
    def _in_dict(base, target):
        base_keys = base.keys()
        target_keys = target.keys()
        if set(base_keys).issubset(target_keys) is False:
            return False

        for key in base.keys():
            target_value = target.get(key, None)
            if target_value != base[key]:
                return False

        return True

if __name__ == '__main__':
    unittest.main()
