# Copyright(c) 2015, Oracle and/or its affiliates.  All Rights Reserved.
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
import logging
import os
import six
import yaml

import kollacli.i18n as u

from kollacli.common.inventory import Inventory
from kollacli.common.utils import change_property
from kollacli.common.utils import get_group_vars_dir
from kollacli.common.utils import get_host_vars_dir
from kollacli.common.utils import get_kolla_etc
from kollacli.common.utils import get_kolla_home
from kollacli.common.utils import sync_read_file
from kollacli.exceptions import CommandError

LOG = logging.getLogger(__name__)

ALLVARS_PATH = 'ansible/group_vars/all.yml'
GLOBALS_FILENAME = 'globals.yml'
ANSIBLE_ROLES_PATH = 'ansible/roles'
ANSIBLE_DEFAULTS_PATH = 'defaults/main.yml'


class AnsibleProperties(object):

    def __init__(self):
        """initialize ansible property information

        property information is pulled from the following files:
        KOLLA_ETC/globals.yml
        KOLLA_ETC/passwords.yml
        KOLLA_HOME/group_vars/all.yml
        KOLLA_HOME/ansible/roles/<service>/default/main.yml
        """
        self.globals_path = ''
        self.global_props = []
        self.unique_global_props = {}
        self.group_props = {}
        self.host_props = {}

        self._load_properties_roles()
        self._load_properties_all()
        self._load_properties_global()
        self._load_properties_hostvars()
        self._load_properties_groupvars()

    def _load_properties_roles(self):
        start_dir = os.path.join(get_kolla_home(), ANSIBLE_ROLES_PATH)
        services = next(os.walk(start_dir))[1]
        for service_name in services:
            file_name = os.path.join(start_dir, service_name,
                                     ANSIBLE_DEFAULTS_PATH)
            if os.path.isfile(file_name):
                with open(file_name) as service_file:
                    service_contents = yaml.safe_load(service_file)
                    prop_file_name = service_name + ':main.yml'
                    for key, value in service_contents.items():
                        ansible_prop = AnsibleProperty(key, value,
                                                       prop_file_name)
                        self.global_props.append(ansible_prop)
                        self.unique_global_props[key] = ansible_prop

    def _load_properties_all(self):
        allvars_path = os.path.join(get_kolla_home(), ALLVARS_PATH)
        with open(allvars_path) as allvars_file:
            allvars_contents = yaml.safe_load(allvars_file)
            for key, value in allvars_contents.items():
                overrides = False
                orig_value = None
                if key in self.unique_global_props:
                    overrides = True
                    orig_value = self.unique_global_props[key].value
                ansible_prop = AnsibleProperty(key, value,
                                               'group_vars/all.yml',
                                               overrides, orig_value)
                self.global_props.append(ansible_prop)
                self.unique_global_props[key] = ansible_prop

    def _load_properties_global(self):
        self.globals_path = os.path.join(get_kolla_etc(), GLOBALS_FILENAME)
        globals_data = sync_read_file(self.globals_path)
        globals_contents = yaml.safe_load(globals_data)
        for key, value in globals_contents.items():
            overrides = False
            orig_value = None
            if key in self.unique_global_props:
                overrides = True
                orig_value = self.unique_global_props[key].value
            ansible_prop = AnsibleProperty(key, value,
                                           GLOBALS_FILENAME,
                                           overrides, orig_value)
            self.global_props.append(ansible_prop)
            self.unique_global_props[key] = ansible_prop

    def _load_properties_hostvars(self):
        host_dir = get_host_vars_dir()
        for hostfile in os.listdir(host_dir):
            self.host_props[hostfile] = []
            with open(os.path.join(host_dir, hostfile)) as host_data:
                host_contents = yaml.safe_load(host_data)
                if host_contents is None:
                    continue
                props = []
                for key, value in host_contents.items():
                    overrides = False
                    orig_value = None
                    if key in self.unique_global_props:
                        overrides = True
                        orig_value = self.unique_global_props[key].value
                    ansible_prop = AnsibleProperty(key, value,
                                                   hostfile,
                                                   overrides, orig_value,
                                                   'host', hostfile)
                    props.append(ansible_prop)
            self.host_props[hostfile] = props

    def _load_properties_groupvars(self):
        group_dir = get_group_vars_dir()
        for groupfile in os.listdir(group_dir):
            if (groupfile == 'all.yml'):
                continue
            self.group_props[groupfile] = []
            with open(os.path.join(group_dir, groupfile)) as group_data:
                group_contents = yaml.safe_load(group_data)
                if group_contents is None:
                    continue
                props = []
                for key, value in group_contents.items():
                    overrides = False
                    orig_value = None
                    if key in self.unique_global_props:
                        overrides = True
                        orig_value = self.unique_global_props[key].value
                    ansible_prop = AnsibleProperty(key, value,
                                                   groupfile,
                                                   overrides, orig_value,
                                                   'group', groupfile)
                    props.append(ansible_prop)
            self.group_props[groupfile] = props

    def get_all(self):
        return sorted(self.global_props, key=lambda x: x.name)

    def get_host_list(self, host_list):
        prop_list = []
        inventory = Inventory.load()
        if host_list is not None:
            for host_name in host_list:
                host = inventory.get_host(host_name)
                if host is None:
                    raise CommandError(
                        u._('Host {host} does not exist.')
                        .format(host=host_name))
                prop_list = prop_list + self.host_props[host_name]
        else:
            hosts = inventory.get_hosts()
            for host in hosts:
                prop_list = prop_list + self.host_props[host.name]
        return prop_list

    def get_group_list(self, group_list):
        prop_list = []
        inventory = Inventory.load()
        if group_list is not None:
            for group_name in group_list:
                group = inventory.get_group(group_name)
                if group is None:
                    raise CommandError(
                        u._('Group {group} does not exist.')
                        .format(group=group_name))
                prop_list = prop_list + self.group_props[group_name]
        else:
            groups = inventory.get_groups()
            for group in groups:
                prop_list = prop_list + self.group_props[group.name]
        return prop_list

    def get_property(self, property_name):
        prop_val = None
        if property_name in self.unique_global_props:
            prop = self.unique_global_props[property_name]
            prop_val = prop.value
        return prop_val

    def get_all_unique(self):
        unique_list = []
        for _, value in self.unique_global_props.items():
            unique_list.append(value)
        return sorted(unique_list, key=lambda x: x.name)

    # TODO(bmace) -- if this isn't used for 2.1.x it should be removed
    # property listing is still being tweaked so leaving for
    # the time being in case we want to use it
    def filter_jinja2(self, contents):
        new_contents = {}
        for key, value in contents.items():
            if not isinstance(value, six.string_types):
                LOG.debug('removing non-string: %s', value)
                continue
            if value and '{{' in value and '}}' in value:
                LOG.debug('removing jinja2 value: %s', value)
                continue
            new_contents[key] = value
        return new_contents

    def set_property(self, property_key, property_value):
        try:
            change_property(self.globals_path, property_key,
                            property_value, clear=False)
        except Exception as e:
            raise e

    def set_host_property(self, property_key, property_value, hosts):
        # if hosts is None set the property on all hosts
        inventory = Inventory.load()
        host_list = []
        if hosts is None:
            host_list = inventory.get_hosts()
        else:
            for host_name in hosts:
                host = inventory.get_host(host_name)
                if host is None:
                    raise CommandError(
                        u._('Host {host} does not exist.')
                        .format(host=host_name))
                host_list.append(host)
        try:
            for host in host_list:
                file_path = os.path.join(get_host_vars_dir(), host.name)
                change_property(file_path, property_key,
                                property_value, clear=False)
        except Exception as e:
            raise e

    def set_group_property(self, property_key, property_value, groups):
        # if groups is None set the property on all hosts
        inventory = Inventory.load()
        group_list = []
        if groups is None:
            group_list = inventory.get_groups()
        else:
            for group_name in groups:
                group = inventory.get_group(group_name)
                if group is None:
                    raise CommandError(
                        u._('Group {group} does not exist.')
                        .format(group=group_name))
                group_list.append(group)
        try:
            for group in group_list:
                file_path = os.path.join(get_group_vars_dir(), group.name)
                change_property(file_path, property_key,
                                property_value, clear=False)
        except Exception as e:
            raise e

    def clear_property(self, property_key):
        try:
            change_property(self.globals_path, property_key,
                            None, clear=True)
        except Exception as e:
            raise e

    def clear_host_property(self, property_key, hosts):
        # if hosts is None set the property on all hosts
        inventory = Inventory.load()
        host_list = []
        if hosts is None:
            host_list = inventory.get_hosts()
        else:
            for host_name in hosts:
                host = inventory.get_host(host_name)
                if host is None:
                    raise CommandError(
                        u._('Host {host} does not exist.')
                        .format(host=host_name))
                host_list.append(host)
        try:
            for host in host_list:
                file_path = os.path.join(get_host_vars_dir(), host.name)
                change_property(file_path, property_key,
                                None, clear=True)
        except Exception as e:
            raise e

    def clear_group_property(self, property_key, groups):
        # if hosts is None set the property on all hosts
        inventory = Inventory.load()
        group_list = []
        if groups is None:
            group_list = inventory.get_groups()
        else:
            for group_name in groups:
                group = inventory.get_group(group_name)
                if group is None:
                    raise CommandError(
                        u._('Group {group} does not exist.')
                        .format(group=group_name))
                group_list.append(group)
        try:
            for group in group_list:
                file_path = os.path.join(get_group_vars_dir(), group.name)
                change_property(file_path, property_key,
                                None, clear=True)
        except Exception as e:
            raise e


class AnsibleProperty(object):

    def __init__(self, name, value, file_name, overrides=False,
                 orig_value=None, prop_type='global', target=None):
        self.name = name
        self.value = value
        self.prop_type = prop_type
        self.file_name = file_name
        self.overrides = overrides
        self.orig_value = orig_value
        self.target = target
