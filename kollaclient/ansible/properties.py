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

from kollaclient.utils import get_kolla_etc
from kollaclient.utils import get_kolla_home


class AnsibleProperties(object):
    log = logging.getLogger(__name__)
    _properties = []
    # this is so for any given property
    # we can look up the file it is in easily, to be used for the
    # property set command
    _file_contents = {}

    def __init__(self):
        """initialize ansible property information

        property information is pulled from the following files:
        KOLLA_ETC/defaults.yml
        KOLLA_ETC/globals.yml
        KOLLA_ETC/passwords.yml
        KOLLA_HOME/ansible/roles/<service>/default/main.yml
        """
        kolla_etc = get_kolla_etc()
        kolla_home = get_kolla_home()

        # to add something do property_dict['key'].append('value')
        try:
            defaults_filename = kolla_etc + 'defaults.yml'
            with open(defaults_filename) as defaults_file:
                defaults_contents = yaml.load(defaults_file)
                self._file_contents[defaults_filename] = defaults_contents
                defaults_contents = self.filter_jinja2(defaults_contents)
                for key, value in defaults_contents.items():
                    ansible_property = AnsibleProperty(key, value,
                                                       'defaults.yml')
                    self._properties.append(ansible_property)
        except Exception as e:
            raise e

        try:
            globals_filename = kolla_etc + '/globals.yml'
            with open(globals_filename) as globals_file:
                globals_contents = yaml.load(globals_file)
                self._file_contents[globals_filename] = globals_contents
                globals_contents = self.filter_jinja2(globals_contents)
                for key, value in globals_contents.items():
                    ansible_property = AnsibleProperty(key, value,
                                                       'globals.yml')
                    self._properties.append(ansible_property)
        except Exception as e:
            raise e

        try:
            start_dir = kolla_home + '/ansible/roles'
            services = next(os.walk(start_dir))[1]
            for service_name in services:
                file_name = start_dir+'/'+service_name+'/defaults/main.yml'
                if os.path.isfile(file_name):
                    with open(file_name) as service_file:
                        service_contents = yaml.load(service_file)
                        self._file_contents[file_name] = service_contents
                        service_contents = self.filter_jinja2(service_contents)
                        prop_file_name = service_name + ':main.yml'
                        for key, value in service_contents.items():
                            ansible_property = AnsibleProperty(key, value,
                                                               prop_file_name)
                            self._properties.append(ansible_property)
        except Exception as e:
            self.log.error('read error:% ' % str(e))

    def get_all(self):
        return self._properties

    def filter_jinja2(self, contents):
        for key, value in contents.items():
            if isinstance(value, basestring) is False:
                self.log.debug('removing non-string: %s' % str(value))
                del contents[key]
                continue
            if value.startswith('{{') and value.endswith('}}'):
                self.log.debug('removing jinja2 value: %s' % value)
                del contents[key]
        return contents


class AnsibleProperty(object):
    name = ''
    value = ''
    file_name = ''

    def __init__(self, name, value, file_name):
        self.name = name
        self.value = value
        self.file_name = file_name
