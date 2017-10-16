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

import kollacli.i18n as u

from kollacli.api.client import ClientApi
from kollacli.api.exceptions import ClientException
from kollacli.commands.exceptions import CommandError
from kollacli.common.utils import convert_lists_to_string

from cliff.command import Command
from cliff.lister import Lister

CLIENT = ClientApi()


class ServiceAddGroup(Command):
    """Add group to service.

    Associated the service to a group. If this is a sub-service,
    the inherit flag will be cleared.
    """

    def get_parser(self, prog_name):
        parser = super(ServiceAddGroup, self).get_parser(prog_name)
        parser.add_argument('servicename', metavar='<servicename>',
                            help=u._('Service name'))
        parser.add_argument('groupname', metavar='<groupname>',
                            help=u._('Group name'))
        return parser

    def take_action(self, parsed_args):
        try:
            groupname = parsed_args.groupname.strip()
            servicename = parsed_args.servicename.strip()

            group = CLIENT.group_get([groupname])[0]
            group.add_service(servicename)

        except ClientException as e:
            raise CommandError(str(e))
        except Exception as e:
            raise Exception(traceback.format_exc())


class ServiceRemoveGroup(Command):
    """Remove group from service."""

    def get_parser(self, prog_name):
        parser = super(ServiceRemoveGroup, self).get_parser(prog_name)
        parser.add_argument('servicename', metavar='<servicename>',
                            help=u._('Service name'))
        parser.add_argument('groupname', metavar='<groupname>',
                            help=u._('Group name'))
        return parser

    def take_action(self, parsed_args):
        try:
            groupname = parsed_args.groupname.strip()
            servicename = parsed_args.servicename.strip()

            group = CLIENT.group_get([groupname])[0]
            group.remove_service(servicename)

        except ClientException as e:
            raise CommandError(str(e))
        except Exception as e:
            raise Exception(traceback.format_exc())


class ServiceListGroups(Lister):
    """List services and their groups."""

    def take_action(self, parsed_args):
        try:
            data = [('', '')]
            services = CLIENT.service_get_all()
            if services:
                data = []
                for service in services:
                    groupnames = sorted(service.get_groups())
                    data.append((service.name, groupnames))

            data = convert_lists_to_string(data, parsed_args)
            return (u._('Service'), u._('Groups')), sorted(data)
        except ClientException as e:
            raise CommandError(str(e))
        except Exception as e:
            raise Exception(traceback.format_exc())


class ServiceList(Lister):
    """List services and their sub-services."""

    def take_action(self, parsed_args):
        try:
            data = [('', '')]
            services = CLIENT.service_get_all()
            if services:
                data = []
                for service in services:
                    data.append((service.name, service.get_children()))

            data = convert_lists_to_string(data, parsed_args)
            return ((u._('Service'), u._('Children')), sorted(data))

        except ClientException as e:
            raise CommandError(str(e))
        except Exception as e:
            raise Exception(traceback.format_exc())
