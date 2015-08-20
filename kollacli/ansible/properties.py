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
from shutil import move
from tempfile import mkstemp
import yaml

from kollacli.utils import get_kolla_etc
from kollacli.utils import get_kolla_home

ALLVARS_PATH = 'ansible/group_vars/all.yml'
GLOBALS_FILENAME = 'globals.yml'
ANSIBLE_ROLES_PATH = 'ansible/roles'
ANSIBLE_DEFAULTS_PATH = 'defaults/main.yml'


class AnsibleProperties(object):
    log = logging.getLogger(__name__)
    _allvars_path = ''
    _globals_path = ''
    _properties = []
    # this is so for any given property
    # we can look up the file it is in easily, to be used for the
    # property set command
    _file_contents = {}

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

        # to add something do property_dict['key'].append('value')
        try:
            self._allvars_path = os.path.join(kolla_home, ALLVARS_PATH)
            with open(self._allvars_path) as allvars_file:
                allvars_contents = yaml.load(allvars_file)
                self._file_contents[self._allvars_path] = allvars_contents
                allvars_contents = self.filter_jinja2(allvars_contents)
                for key, value in allvars_contents.items():
                    ansible_property = AnsibleProperty(key, value,
                                                       'group_vars/all.yml')
                    self._properties.append(ansible_property)
        except Exception as e:
            raise e

        try:
            self._globals_path = os.path.join(kolla_etc, GLOBALS_FILENAME)
            with open(self._globals_path) as globals_file:
                globals_contents = yaml.load(globals_file)
                self._file_contents[self._globals_path] = globals_contents
                globals_contents = self.filter_jinja2(globals_contents)
                for key, value in globals_contents.items():
                    ansible_property = AnsibleProperty(key, value,
                                                       GLOBALS_FILENAME)
                    self._properties.append(ansible_property)
        except Exception as e:
            raise e

        try:
            start_dir = os.path.join(kolla_home, ANSIBLE_ROLES_PATH)
            services = next(os.walk(start_dir))[1]
            for service_name in services:
                file_name = os.path.join(start_dir, service_name,
                                         ANSIBLE_DEFAULTS_PATH)
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
            raise e

    def get_all(self):
        sorted_properties = sorted(self._properties, key=lambda x: x.name)
        return sorted_properties

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
        contents = self._file_contents[self._globals_path]
        try:
            if contents is not None:
                if property_key in contents:
                    self._change_property(property_key, property_value)
                else:
                    self._change_property(property_key, property_value,
                                          append=True)
            else:
                self._change_property(property_key, property_value,
                                      append=True)
        except Exception as e:
            raise e

    def clear_property(self, property_key):
        # We only manipulate values in the globals.yml file so if the variable
        # does not exist we will do nothing.  if it does exist we need to find
        # the line and nuke it.
        contents = self._file_contents[self._globals_path]
        if contents is not None:
            if property_key in contents:
                self._change_property(property_key, None, clear=True)
                # TODO(bmace) do we want any sort of message if we try to clear
                # a property that doesn't exist?

    def _change_property(self, property_key, property_value, append=False,
                         clear=False):
        try:
            # the file handle returned from mkstemp must be closed or else
            # if this is called many times you will have an unpleasant
            # file handle leak
            tmp_filehandle, tmp_path = mkstemp()
            with open(tmp_path, 'w') as tmp_file:
                with open(self._globals_path) as globals_file:
                    new_line = '%s: "%s"\n' % (property_key, property_value)
                    for line in globals_file:
                        if append is False:
                            if line.startswith(property_key):
                                if clear:
                                    line = ''
                                else:
                                    line = new_line
                            tmp_file.write(line)
                        else:
                            tmp_file.write(line)
                    if append is True:
                        tmp_file.write(new_line)

            os.remove(self._globals_path)
            move(tmp_path, self._globals_path)
        except Exception as e:
            raise e
        finally:
            try:
                os.close(tmp_filehandle)
            except Exception:
                pass

            if tmp_filehandle is not None:
                try:
                    os.close(tmp_filehandle)
                except Exception:
                    pass

            if tmp_path is not None:
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass


class AnsibleProperty(object):
    name = ''
    value = ''
    file_name = ''

    def __init__(self, name, value, file_name):
        self.name = name
        self.value = value
        self.file_name = file_name
