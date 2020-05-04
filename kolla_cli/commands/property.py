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

import traceback

from cliff.command import Command
from cliff.lister import Lister

from kolla_cli.api.client import ClientApi
from kolla_cli.commands.exceptions import CommandError
from kolla_cli.common import utils
import kolla_cli.i18n as u

CLIENT = ClientApi()


def _get_names(args_list):
    csv_list = args_list[0].strip()
    names = csv_list.split(',')
    if 'all' in names:
        names = None
    return names


class PropertySet(Command):
    "Property Set"

    def get_parser(self, prog_name):
        parser = super(PropertySet, self).get_parser(prog_name)
        parser.add_argument('propertyname', metavar='<propertyname>',
                            help=u._('Property name'))
        parser.add_argument('propertyvalue', metavar='<propertyvalue',
                            help=u._('Property value'))
        parser.add_argument('--hosts', nargs=1,
                            metavar='<host_list>',
                            help=u._('Property host list'))
        parser.add_argument('--groups', nargs=1,
                            metavar='<group_list>',
                            help=u._('Property group list'))
        return parser

    def take_action(self, parsed_args):
        try:
            property_name = parsed_args.propertyname.strip()
            property_value = parsed_args.propertyvalue.strip()
            property_dict = {}
            property_dict[property_name] = property_value

            if parsed_args.hosts:
                if parsed_args.groups:
                    raise CommandError(
                        u._('Invalid to use both hosts and groups arguments '
                            'together.'))

                host_names = _get_names(parsed_args.hosts)

                CLIENT.property_set(property_dict,
                                    'host', host_names)

            elif parsed_args.groups:
                group_names = _get_names(parsed_args.groups)

                CLIENT.property_set(property_dict,
                                    'group', group_names)
            else:
                CLIENT.property_set(property_dict,
                                    'global')

        except Exception:
            raise Exception(traceback.format_exc())


class PropertyClear(Command):
    "Property Clear"

    def get_parser(self, prog_name):
        parser = super(PropertyClear, self).get_parser(prog_name)
        parser.add_argument('propertyname', metavar='<propertyname>',
                            help=u._('Property name'))
        parser.add_argument('--hosts', nargs=1,
                            metavar='<host_list>',
                            help=u._('Property host list'))
        parser.add_argument('--groups', nargs=1,
                            metavar='<group_list>',
                            help=u._('Property group list'))
        return parser

    def take_action(self, parsed_args):
        try:
            property_name = parsed_args.propertyname.strip()
            property_list = []
            property_list.append(property_name)

            if parsed_args.hosts:
                if parsed_args.groups:
                    raise CommandError(
                        u._('Invalid to use both hosts and groups arguments '
                            'together.'))

                host_names = _get_names(parsed_args.hosts)

                CLIENT.property_clear(property_list, 'host',
                                      host_names)
            elif parsed_args.groups:
                group_names = _get_names(parsed_args.groups)

                CLIENT.property_clear(property_list, 'group',
                                      group_names)
            else:
                CLIENT.property_clear(property_list, 'global')

        except Exception:
            raise Exception(traceback.format_exc())


class PropertyList(Lister):
    """List all properties."""

    def __init__(self, app, app_args, cmd_name=None):
        super(Lister, self).__init__(app, app_args,
                                     cmd_name=cmd_name)

        self.is_global = True
        self.is_all_flag = False
        self.is_long_flag = False
        self.list_type = None

    def get_parser(self, prog_name):
        parser = super(PropertyList, self).get_parser(prog_name)
        parser.add_argument('--all', action='store_true',
                            help=u._('List all properties'))
        parser.add_argument('--long', action='store_true',
                            help=u._('Show all property attributes'))
        parser.add_argument('--hosts', nargs=1,
                            metavar='<host_list>',
                            help=u._('Property host list'))
        parser.add_argument('--groups', nargs=1,
                            metavar='<group_list>',
                            help=u._('Property group list'))
        return parser

    def take_action(self, parsed_args):
        try:
            if parsed_args.all:
                self.is_all_flag = True
            if parsed_args.long:
                self.is_long_flag = True

            if parsed_args.hosts:
                if parsed_args.groups:
                    raise CommandError(
                        u._('Invalid to use both hosts and groups arguments '
                            'together.'))

                self.is_global = False
                self.list_type = u._('Host')
                host_names = _get_names(parsed_args.hosts)

                property_list = CLIENT.property_get('host',
                                                    host_names)

            elif parsed_args.groups:
                self.is_global = False
                self.list_type = u._('Group')
                group_names = _get_names(parsed_args.groups)
                property_list = CLIENT.property_get('group',
                                                    group_names)

            else:
                property_list = CLIENT.property_get('global')

            data = self._get_list_data(property_list)
            header = self._get_list_header()
            return (header, data)

        except Exception:
            raise Exception(traceback.format_exc())

    def _get_list_header(self):
        header = None
        if self.is_long_flag:
            if self.is_global:
                header = (u._('OVR'),
                          u._('Property Name'), u._('Property Value'),
                          u._('Original Value'))
            else:
                header = (u._('OVR'),
                          u._('Property Name'), u._('Property Value'),
                          u._('Original Value'),
                          self.list_type)
        else:
            if self.is_global:
                header = (u._('OVR'),
                          u._('Property Name'), u._('Property Value'))
            else:
                header = (u._('OVR'),
                          u._('Property Name'), u._('Property Value'),
                          self.list_type)
        return header

    def _get_list_data(self, property_list):
        data = []
        if property_list:
            property_length = utils.get_property_list_length()
            for prop in property_list:
                include_prop = False
                if (prop.value is not None and
                        len(str(prop.value)) > property_length):
                    if self.is_all_flag:
                        include_prop = True
                else:
                    include_prop = True

                if not include_prop:
                    continue

                ovr_global = '-'
                ovr_group = '-'
                ovr_host = '-'

                if prop.ovr_global:
                    ovr_global = '*'
                if prop.ovr_group:
                    ovr_group = 'G'
                if prop.ovr_host:
                    ovr_host = 'H'

                prop_ovr = ovr_global + ovr_group + ovr_host

                if self.is_long_flag:
                    if self.is_global:
                        data.append((prop_ovr, prop.name, prop.value,
                                     prop.orig_value))
                    else:
                        data.append((prop_ovr, prop.name, prop.value,
                                     prop.orig_value, prop.target))
                else:
                    if self.is_global:
                        data.append((prop_ovr, prop.name, prop.value))
                    else:
                        data.append((prop_ovr, prop.name, prop.value,
                                     prop.target))
        else:
            if self.is_long_flag:
                if self.is_global:
                    data.append(('', '', '', ''))
                else:
                    data.append(('', '', '', '', ''))
            else:
                if self.is_global:
                    data.append(('', '', ''))
                else:
                    data.append(('', '', '', ''))

        return data
