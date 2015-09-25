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
import yaml

from kollacli.utils import change_property
from kollacli.utils import get_kolla_etc
from kollacli.utils import get_kolla_home

ALLVARS_PATH = 'ansible/group_vars/all.yml'
GLOBALS_FILENAME = 'globals.yml'
ANSIBLE_ROLES_PATH = 'ansible/roles'
ANSIBLE_DEFAULTS_PATH = 'defaults/main.yml'


class AnsibleProperties(object):
    log = logging.getLogger(__name__)

    def __init__(self):
        """initialize ansible property information

        property information is pulled from the following files:
        KOLLA_ETC/globals.yml
        KOLLA_ETC/passwords.yml
        KOLLA_HOME/group_vars/all.yml
        KOLLA_HOME/ansible/roles/<service>/default/main.yml
        """
        kolla_etc = get_kolla_etc()
        kolla_home = get_kolla_home()

        self.allvars_path = ''
        self.globals_path = ''
        self.properties = []
        self.unique_properties = {}
        # this is so for any given property
        # we can look up the file it is in easily, to be used for the
        # property set command
        self.file_contents = {}

        try:
            start_dir = os.path.join(kolla_home, ANSIBLE_ROLES_PATH)
            services = next(os.walk(start_dir))[1]
            for service_name in services:
                file_name = os.path.join(start_dir, service_name,
                                         ANSIBLE_DEFAULTS_PATH)
                if os.path.isfile(file_name):
                    with open(file_name) as service_file:
                        service_contents = yaml.load(service_file)
                        self.file_contents[file_name] = service_contents
                        service_contents = self.filter_jinja2(service_contents)
                        prop_file_name = service_name + ':main.yml'
                        for key, value in service_contents.items():
                            ansible_property = AnsibleProperty(key, value,
                                                               prop_file_name)
                            self.properties.append(ansible_property)
                            self.unique_properties[key] = ansible_property
        except Exception as e:
            raise e

        try:
            self.allvars_path = os.path.join(kolla_home, ALLVARS_PATH)
            with open(self.allvars_path) as allvars_file:
                allvars_contents = yaml.load(allvars_file)
                self.file_contents[self.allvars_path] = allvars_contents
                allvars_contents = self.filter_jinja2(allvars_contents)
                for key, value in allvars_contents.items():
                    ansible_property = AnsibleProperty(key, value,
                                                       'group_vars/all.yml')
                    self.properties.append(ansible_property)
                    self.unique_properties[key] = ansible_property
        except Exception as e:
            raise e

        try:
            self.globals_path = os.path.join(kolla_etc, GLOBALS_FILENAME)
            with open(self.globals_path) as globals_file:
                globals_contents = yaml.load(globals_file)
                self.file_contents[self.globals_path] = globals_contents
                globals_contents = self.filter_jinja2(globals_contents)
                for key, value in globals_contents.items():
                    ansible_property = AnsibleProperty(key, value,
                                                       GLOBALS_FILENAME)
                    self.properties.append(ansible_property)
                    self.unique_properties[key] = ansible_property
        except Exception as e:
            raise e

    def get_all(self):
        return sorted(self.properties, key=lambda x: x.name)

    def get_property(self, property_name):
        prop_val = None
        if property_name in self.unique_properties:
            prop = self.unique_properties[property_name]
            prop_val = prop.value
        return prop_val

    def get_all_unique(self):
        unique_list = []
        for _, value in self.unique_properties.items():
            unique_list.append(value)
        return sorted(unique_list, key=lambda x: x.name)

    def filter_jinja2(self, contents):
        for key, value in contents.items():
            if isinstance(value, basestring) is False:
                self.log.debug('removing non-string: %s' % str(value))
                del contents[key]
                continue
            if '{{' in value and '}}' in value:
                self.log.debug('removing jinja2 value: %s' % value)
                del contents[key]
        return contents

    def set_property(self, property_key, property_value):
        # We only manipulate values in the globals.yml file so look up the key
        # and if it is there, we will parse through the file to replace that
        # line.  if the key doesn't exist we append to the end of the file
        try:
            change_property(self.globals_path, property_key,
                            property_value, clear=False)
        except Exception as e:
            raise e

    def clear_property(self, property_key):
        # We only manipulate values in the globals.yml file so if the variable
        # does not exist we will do nothing.  if it does exist we need to find
        # the line and nuke it.
        try:
            change_property(self.globals_path, property_key,
                            None, clear=True)
        except Exception as e:
            raise e


class AnsibleProperty(object):

    def __init__(self, name, value, file_name):
        self.name = name
        self.value = value
        self.file_name = file_name
