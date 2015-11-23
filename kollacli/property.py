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
import traceback

import kollacli.i18n as u

from kollacli.common import properties

from cliff.command import Command
from cliff.lister import Lister


class PropertySet(Command):
    "Property Set"

    def get_parser(self, prog_name):
        parser = super(PropertySet, self).get_parser(prog_name)
        parser.add_argument('propertyname', metavar='<propertyname>',
                            help=u._('Property name'))
        parser.add_argument('propertyvalue', metavar='<propertyvalue',
                            help=u._('Property value'))
        return parser

    def take_action(self, parsed_args):
        try:
            property_name = parsed_args.propertyname.strip()
            property_value = parsed_args.propertyvalue.strip()

            ansible_properties = properties.AnsibleProperties()
            ansible_properties.set_property(property_name, property_value)
        except Exception:
            raise Exception(traceback.format_exc())


class PropertyClear(Command):
    "Property Clear"

    def get_parser(self, prog_name):
        parser = super(PropertyClear, self).get_parser(prog_name)
        parser.add_argument('propertyname', metavar='<propertyname>',
                            help=u._('Property name'))
        return parser

    def take_action(self, parsed_args):
        try:
            property_name = parsed_args.propertyname.strip()

            ansible_properties = properties.AnsibleProperties()
            ansible_properties.clear_property(property_name)
        except Exception:
            raise Exception(traceback.format_exc())


class PropertyList(Lister):
    """List all properties"""

    def take_action(self, parsed_args):
        ansible_properties = properties.AnsibleProperties()
        property_list = ansible_properties.get_all_unique()
        data = []
        if property_list:
            for value in property_list:
                data.append((value.name, value.value))
        else:
            data.append(('', ''))

        return ((u._('Property Name'), u._('Property Value')), data)
