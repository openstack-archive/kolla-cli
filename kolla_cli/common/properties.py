# Copyright(c) 2016, Oracle and/or its affiliates.  All Rights Reserved.
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

import copy
import logging
import os
import yaml

from kolla_cli.api.exceptions import NotInInventory
from kolla_cli.common.inventory import Inventory
from kolla_cli.common.utils import change_property
from kolla_cli.common.utils import get_group_vars_dir
from kolla_cli.common.utils import get_host_vars_dir
from kolla_cli.common.utils import get_kolla_ansible_home
from kolla_cli.common.utils import sync_read_file
import kolla_cli.i18n as u

LOG = logging.getLogger(__name__)

ALLVARS_PATH = 'ansible/group_vars/all.yml'
GLOBALS_PATH = 'ansible/group_vars/__GLOBAL__'
ANSIBLE_ROLES_PATH = 'ansible/roles'
ANSIBLE_DEFAULTS_PATH = 'defaults/main.yml'


class AnsibleProperties(object):

    def __init__(self):
        """initialize ansible property information

        property information is pulled from the following files
        (from lowest to highest priority):
        KOLLA_HOME/ansible/roles/<service>/default/main.yml
        KOLLA_HOME/ansible/group_vars/all.yml
        KOLLA_HOME/ansible/group_vars/__GLOBAL__
        KOLLA_HOME/ansible/group_vars/*
        KOLLA_HOME/ansible/host_vars/*
        KOLLA_ETC/passwords.yml
        """
        self.globals_path = os.path.join(get_kolla_ansible_home(),
                                         GLOBALS_PATH)
        self.global_props = []
        self.unique_global_props = {}
        self.unique_override_flags = {}
        self.group_props = {}
        self.host_props = {}
        self.properties_loaded = False
        self._inventory = None

    def _load_properties(self):
        self._load_inventory()
        if not self.properties_loaded:
            self._load_properties_roles()
            self._load_properties_all()
            self._load_properties_global()
            self._load_properties_hostvars()
            self._load_properties_groupvars()
            self.properties_loaded = True

    def _load_properties_roles(self):
        start_dir = os.path.join(get_kolla_ansible_home(), ANSIBLE_ROLES_PATH)
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
        allvars_path = os.path.join(get_kolla_ansible_home(), ALLVARS_PATH)
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
        globals_data = sync_read_file(self.globals_path)
        globals_contents = yaml.safe_load(globals_data)
        if not globals_contents:
            return
        for key, value in globals_contents.items():
            overrides = False
            override_flags = OverrideFlags()
            orig_value = None
            if key in self.unique_global_props:
                overrides = True
                override_flags.ovr_global = True
                orig_value = self.unique_global_props[key].value
            ansible_prop = AnsibleProperty(key, value,
                                           'group_vars/__GLOBAL__',
                                           overrides, orig_value)
            ansible_prop.override_flags = override_flags
            self.global_props.append(ansible_prop)
            self.unique_global_props[key] = ansible_prop
            self.unique_override_flags[key] = override_flags

    def _load_properties_hostvars(self):
        host_dir = get_host_vars_dir()
        hostnames = self._inventory.get_hostnames()
        for hostfile in os.listdir(host_dir):
            if hostfile not in hostnames:
                # skip any host files that don't match existing hosts
                continue
            self.host_props[hostfile] = []
            with open(os.path.join(host_dir, hostfile)) as host_data:
                host_contents = yaml.safe_load(host_data)
                if host_contents is None:
                    continue
                props = []
                for key, value in host_contents.items():
                    overrides = False
                    override_flags = OverrideFlags()
                    if key in self.unique_override_flags:
                        override_flags = self.unique_override_flags[key]
                    orig_value = None
                    if key in self.unique_global_props:
                        overrides = True
                        override_flags.ovr_host = True
                        self.unique_override_flags[key] = override_flags
                        orig_value = self.unique_global_props[key].value
                    ansible_prop = AnsibleProperty(key, value,
                                                   hostfile,
                                                   overrides, orig_value,
                                                   'host', hostfile)
                    props.append(ansible_prop)
            self.host_props[hostfile] = props

    def _load_properties_groupvars(self):
        group_dir = get_group_vars_dir()
        groupnames = self._inventory.get_groupnames()
        for groupfile in os.listdir(group_dir):
            if groupfile not in groupnames:
                # skip any files that don't match existing groups
                continue
            with open(os.path.join(group_dir, groupfile)) as group_data:
                group_contents = yaml.safe_load(group_data)
                if group_contents is None:
                    continue
                props = []
                for key, value in group_contents.items():
                    overrides = False
                    override_flags = OverrideFlags()
                    if key in self.unique_override_flags:
                        override_flags = self.unique_override_flags[key]
                    orig_value = None
                    if key in self.unique_global_props:
                        overrides = True
                        override_flags.ovr_group = True
                        self.unique_override_flags[key] = override_flags
                        orig_value = self.unique_global_props[key].value
                    ansible_prop = AnsibleProperty(key, value,
                                                   groupfile,
                                                   overrides, orig_value,
                                                   'group', groupfile)
                    props.append(ansible_prop)
            self.group_props[groupfile] = props

    def _load_inventory(self):
        if not self._inventory:
            self._inventory = Inventory.load()  # nosec

    def get_host_list(self, host_list):
        self._load_properties()
        prop_list = []
        if host_list is not None:
            for host_name in host_list:
                host = self._inventory.get_host(host_name)
                if host is None:
                    raise NotInInventory(u._('Host'), host_name)
                if host_name in self.host_props:
                    prop_list += self.host_props[host_name]
        else:
            hosts = self._inventory.get_hosts()
            for host in hosts:
                if host.name in self.host_props:
                    prop_list += self.host_props[host.name]
        return prop_list

    def get_group_list(self, group_list):
        self._load_properties()
        prop_list = []
        if group_list is not None:
            for group_name in group_list:
                group = self._inventory.get_group(group_name)
                if group is None:
                    raise NotInInventory(u._('Group'), group_name)
                if group_name in self.group_props:
                    prop_list += self.group_props[group_name]
        else:
            groups = self._inventory.get_groups()
            for group in groups:
                if group.name in self.group_props:
                    prop_list += self.group_props[group.name]
        return prop_list

    def get_property_value(self, property_name):
        self._load_properties()
        prop_val = None
        if property_name in self.unique_global_props:
            prop = self.unique_global_props[property_name]
            prop_val = prop.value
        return prop_val

    def get_property(self, property_name):
        self._load_properties()
        return self.unique_global_props.get(property_name)

    def get_all_unique(self):
        self._load_properties()
        unique_list = []
        for _, value in self.unique_global_props.items():
            unique_list.append(value)
        return sorted(unique_list, key=lambda x: x.name)

    def get_all_override_flags(self):
        self._load_properties()
        return self.unique_override_flags

    def set_property(self, property_dict):
        change_property(self.globals_path, property_dict,
                        clear=False)

    def set_host_property(self, property_dict, hosts):
        # if hosts is None set the property on all hosts
        self._load_inventory()
        host_list = []
        if hosts is None:
            host_list = self._inventory.get_hosts()
        else:
            for host_name in hosts:
                host = self._inventory.get_host(host_name)
                if host is None:
                    raise NotInInventory(u._('Host'), host_name)
                host_list.append(host)
        try:
            for host in host_list:
                file_path = os.path.join(get_host_vars_dir(), host.name)
                change_property(file_path, property_dict,
                                clear=False)
        except Exception as e:
            raise e

    def set_group_property(self, property_dict, groups):
        # if groups is None set the property on all hosts
        self._load_inventory()
        group_list = []
        if groups is None:
            group_list = self._inventory.get_groups()
        else:
            for group_name in groups:
                group = self._inventory.get_group(group_name)
                if group is None:
                    raise NotInInventory(u._('Group'), group_name)
                group_list.append(group)
        try:
            for group in group_list:
                tmp_dict = copy.copy(property_dict)
                file_path = os.path.join(get_group_vars_dir(), group.name)
                change_property(file_path, tmp_dict,
                                clear=False)
        except Exception as e:
            raise e

    def clear_property(self, property_list):
        try:
            change_property(self.globals_path,
                            self._list_to_dict(property_list),
                            clear=True)
        except Exception as e:
            raise e

    def clear_host_property(self, property_list, hosts):
        # if hosts is None set the property on all hosts
        self._load_inventory()
        host_list = []
        if hosts is None:
            host_list = self._inventory.get_hosts()
        else:
            for host_name in hosts:
                host = self._inventory.get_host(host_name)
                if host is None:
                    raise NotInInventory(u._('Host'), host_name)
                host_list.append(host)
        try:
            for host in host_list:
                file_path = os.path.join(get_host_vars_dir(), host.name)
                change_property(file_path, self._list_to_dict(property_list),
                                clear=True)
        except Exception as e:
            raise e

    def clear_group_property(self, property_list, groups):
        # if hosts is None set the property on all hosts
        self._load_inventory()
        group_list = []
        if groups is None:
            group_list = self._inventory.get_groups()
        else:
            for group_name in groups:
                group = self._inventory.get_group(group_name)
                if group is None:
                    raise NotInInventory(u._('Group'), group_name)
                group_list.append(group)
        try:
            for group in group_list:
                file_path = os.path.join(get_group_vars_dir(), group.name)
                change_property(file_path, self._list_to_dict(property_list),
                                clear=True)
        except Exception as e:
            raise e

    def _list_to_dict(self, property_list):
        property_dict = {}
        for key in property_list:
            property_dict[key] = ''
        return property_dict


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
        self.value_type = type(value)


class OverrideFlags(object):

    def __init__(self):
        self.ovr_global = False
        self.ovr_group = False
        self.ovr_host = False
