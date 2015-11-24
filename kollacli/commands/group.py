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

from kollacli.common.inventory import Inventory
from kollacli.common.utils import convert_to_unicode
from kollacli.exceptions import CommandError

from cliff.command import Command
from cliff.lister import Lister


class GroupAdd(Command):
    """Add group to open-stack-kolla"""
    def get_parser(self, prog_name):
        parser = super(GroupAdd, self).get_parser(prog_name)
        parser.add_argument('groupname', metavar='<groupname>',
                            help=u._('Group name'))
        return parser

    def take_action(self, parsed_args):
        try:
            groupname = parsed_args.groupname.strip()
            groupname = convert_to_unicode(groupname)

            inventory = Inventory.load()
            inventory.add_group(groupname)
            Inventory.save(inventory)
        except CommandError as e:
            raise e
        except Exception as e:
            raise Exception(traceback.format_exc())


class GroupRemove(Command):
    """Remove group from openstack-kolla"""

    def get_parser(self, prog_name):
        parser = super(GroupRemove, self).get_parser(prog_name)
        parser.add_argument('groupname', metavar='<groupname>',
                            help=u._('Group name'))
        return parser

    def take_action(self, parsed_args):
        try:
            groupname = parsed_args.groupname.strip()
            groupname = convert_to_unicode(groupname)
            inventory = Inventory.load()
            inventory.remove_group(groupname)
            Inventory.save(inventory)
        except CommandError as e:
            raise e
        except Exception as e:
            raise Exception(traceback.format_exc())


class GroupAddhost(Command):
    """Add host to group"""
    def get_parser(self, prog_name):
        parser = super(GroupAddhost, self).get_parser(prog_name)
        parser.add_argument('groupname', metavar='<groupname>',
                            help=u._('Group name'))
        parser.add_argument('hostname', metavar='<hostname>',
                            help=u._('Host name'))
        return parser

    def take_action(self, parsed_args):
        try:
            groupname = parsed_args.groupname.strip()
            groupname = convert_to_unicode(groupname)
            hostname = parsed_args.hostname.strip()
            hostname = convert_to_unicode(hostname)
            inventory = Inventory.load()
            inventory.add_host(hostname, groupname)
            Inventory.save(inventory)
        except CommandError as e:
            raise e
        except Exception as e:
            raise Exception(traceback.format_exc())


class GroupRemovehost(Command):
    """Remove host group from group"""

    def get_parser(self, prog_name):
        parser = super(GroupRemovehost, self).get_parser(prog_name)
        parser.add_argument('groupname', metavar='<groupname>',
                            help=u._('Group name'))
        parser.add_argument('hostname', metavar='<hostname>',
                            help=u._('Host name'))
        return parser

    def take_action(self, parsed_args):
        try:
            groupname = parsed_args.groupname.strip()
            groupname = convert_to_unicode(groupname)
            hostname = parsed_args.hostname.strip()
            hostname = convert_to_unicode(hostname)

            inventory = Inventory.load()
            inventory.remove_host(hostname, groupname)
            Inventory.save(inventory)
        except CommandError as e:
            raise e
        except Exception as e:
            raise Exception(traceback.format_exc())


class GroupListhosts(Lister):
    """List all groups and their hosts"""

    def take_action(self, parsed_args):
        try:
            inventory = Inventory.load()

            data = []
            group_hosts = inventory.get_group_hosts()
            if group_hosts:
                for (groupname, hostnames) in group_hosts.items():
                    data.append((groupname, hostnames))
            else:
                data.append(('', ''))
            return ((u._('Group'), u._('Hosts')), sorted(data))
        except CommandError as e:
            raise e
        except Exception as e:
            raise Exception(traceback.format_exc())


class GroupAddservice(Command):
    """Add service to group"""
    def get_parser(self, prog_name):
        parser = super(GroupAddservice, self).get_parser(prog_name)
        parser.add_argument('groupname', metavar='<groupname>',
                            help=u._('Group name'))
        parser.add_argument('servicename', metavar='<servicename>',
                            help=u._('Service name'))
        return parser

    def take_action(self, parsed_args):
        try:
            groupname = parsed_args.groupname.strip()
            groupname = convert_to_unicode(groupname)
            servicename = parsed_args.servicename.strip()
            servicename = convert_to_unicode(servicename)

            inventory = Inventory.load()
            inventory.add_group_to_service(groupname, servicename)
            Inventory.save(inventory)
        except CommandError as e:
            raise e
        except Exception as e:
            raise Exception(traceback.format_exc())


class GroupRemoveservice(Command):
    """Remove service group from group"""

    def get_parser(self, prog_name):
        parser = super(GroupRemoveservice, self).get_parser(prog_name)
        parser.add_argument('groupname', metavar='<groupname>',
                            help=u._('Group name'))
        parser.add_argument('servicename', metavar='<servicename>',
                            help=u._('Service name'))
        return parser

    def take_action(self, parsed_args):
        try:
            groupname = parsed_args.groupname.strip()
            groupname = convert_to_unicode(groupname)
            servicename = parsed_args.servicename.strip()
            servicename = convert_to_unicode(servicename)

            inventory = Inventory.load()
            inventory.remove_group_from_service(groupname, servicename)
            Inventory.save(inventory)
        except CommandError as e:
            raise e
        except Exception as e:
            raise Exception(traceback.format_exc())


class GroupListservices(Lister):
    """List all groups and their services"""

    def take_action(self, parsed_args):
        try:
            inventory = Inventory.load()

            data = []
            group_services = inventory.get_group_services()
            if group_services:
                for (groupname, servicenames) in group_services.items():
                    data.append((groupname, sorted(servicenames)))
            else:
                data.append(('', ''))
            return ((u._('Group'), u._('Services')), sorted(data))
        except CommandError as e:
            raise e
        except Exception as e:
            raise Exception(traceback.format_exc())
