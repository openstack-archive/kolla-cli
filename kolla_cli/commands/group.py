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
from kolla_cli.api.exceptions import ClientException
from kolla_cli.commands.exceptions import CommandError
from kolla_cli.common.utils import convert_lists_to_string
import kolla_cli.i18n as u

CLIENT = ClientApi()


class GroupAdd(Command):
    """Add group to openstack-kolla."""
    def get_parser(self, prog_name):
        parser = super(GroupAdd, self).get_parser(prog_name)
        parser.add_argument('groupname', metavar='<groupname>',
                            help=u._('Group name'))
        return parser

    def take_action(self, parsed_args):
        try:
            groupname = parsed_args.groupname.strip()

            CLIENT.group_add([groupname])
        except ClientException as e:
            raise CommandError(str(e))
        except Exception:
            raise Exception(traceback.format_exc())


class GroupRemove(Command):
    """Remove group from openstack-kolla."""

    def get_parser(self, prog_name):
        parser = super(GroupRemove, self).get_parser(prog_name)
        parser.add_argument('groupname', metavar='<groupname>',
                            help=u._('Group name'))
        return parser

    def take_action(self, parsed_args):
        try:
            groupname = parsed_args.groupname.strip()

            CLIENT.group_remove([groupname])
        except ClientException as e:
            raise CommandError(str(e))
        except Exception:
            raise Exception(traceback.format_exc())


class GroupAddhost(Command):
    """Add host to group."""
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
            hostname = parsed_args.hostname.strip()

            group = CLIENT.group_get([groupname])[0]
            group.add_host(hostname)

        except ClientException as e:
            raise CommandError(str(e))
        except Exception:
            raise Exception(traceback.format_exc())


class GroupRemovehost(Command):
    """Remove host group from group."""

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
            hostname = parsed_args.hostname.strip()

            group = CLIENT.group_get([groupname])[0]
            group.remove_host(hostname)

        except ClientException as e:
            raise CommandError(str(e))
        except Exception:
            raise Exception(traceback.format_exc())


class GroupList(Lister):
    """Only list all groups """

    def take_action(self, parsed_args):
        try:
            data = [('',)]
            groups = CLIENT.group_get_all()
            if groups:
                data = []
                for group in groups:
                    data.append((group.get_name(),))
            data = convert_lists_to_string(data, parsed_args)
            return ((u._('Group'), ), sorted(data))
        except ClientException as e:
            raise CommandError(str(e))
        except Exception:
            raise Exception(traceback.format_exc())


class GroupListhosts(Lister):
    """List all groups and their hosts."""

    def take_action(self, parsed_args):
        try:
            data = [('', '')]
            groups = CLIENT.group_get_all()
            if groups:
                data = []
                for group in groups:
                    data.append((group.get_name(),
                                 sorted(group.get_hosts())))
            data = convert_lists_to_string(data, parsed_args)
            return ((u._('Group'), u._('Hosts')), sorted(data))
        except ClientException as e:
            raise CommandError(str(e))
        except Exception:
            raise Exception(traceback.format_exc())


class GroupListservices(Lister):
    """List all groups and their services."""

    def take_action(self, parsed_args):
        try:
            data = [('', '')]
            groups = CLIENT.group_get_all()
            if groups:
                data = []
                for group in groups:
                    data.append((group.get_name(),
                                 sorted(group.get_services())))
            data = convert_lists_to_string(data, parsed_args)
            return ((u._('Group'), u._('Services')), sorted(data))
        except ClientException as e:
            raise CommandError(str(e))
        except Exception:
            raise Exception(traceback.format_exc())
