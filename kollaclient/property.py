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

from kollaclient.ansible import properties
from kollaclient.i18n import _

from cliff.command import Command
from cliff.lister import Lister


class PropertySet(Command):
    "Property Set"

    log = logging.getLogger(__name__)

    def take_action(self, parsed_args):
        self.log.info(_("property set"))


class PropertyList(Lister):
    """List all properties"""

    log = logging.getLogger(__name__)

    def take_action(self, parsed_args):
        ansible_properties = properties.AnsibleProperties()
        property_list = ansible_properties.get_all()
        data = []
        if property_list:
            for value in property_list:
                data.append((value.name, value.value, value.file_name))
        else:
            data.append(('', '', ''))

        return (('Property Name', 'Property Value', 'File'), data)
