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
from kollacli.exceptions import CommandError
from kollacli import utils

from cliff.command import Command
from cliff.lister import Lister


class ServiceAddGroup(Command):
    """Add group to service

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
            groupname = utils.convert_to_unicode(groupname)
            servicename = parsed_args.servicename.strip()
            servicename = utils.convert_to_unicode(servicename)

            inventory = Inventory.load()

            inventory.add_group_to_service(groupname, servicename)

            Inventory.save(inventory)
        except CommandError as e:
            raise e
        except Exception as e:
            raise Exception(traceback.format_exc())


class ServiceRemoveGroup(Command):
    """Remove group from service"""

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
            groupname = utils.convert_to_unicode(groupname)
            servicename = parsed_args.servicename.strip()
            servicename = utils.convert_to_unicode(servicename)

            inventory = Inventory.load()

            inventory.remove_group_from_service(groupname, servicename)

            Inventory.save(inventory)
        except CommandError as e:
            raise e
        except Exception as e:
            raise Exception(traceback.format_exc())


class ServiceListGroups(Lister):
    """List services and their groups"""

    def take_action(self, parsed_args):
        try:
            inventory = Inventory.load()

            data = []
            service_groups = inventory.get_service_groups()
            if service_groups:
                for (servicename, (groupnames, inherit)) \
                        in service_groups.items():
                    inh_str = 'yes'
                    if inherit is None:
                        inh_str = '-'
                    elif inherit is False:
                        inh_str = 'no'
                    data.append((servicename, groupnames, inh_str))
            else:
                data.append(('', ''))
            return ((u._('Service'), u._('Groups'), u._('Inherited')),
                    sorted(data))
        except CommandError as e:
            raise e
        except Exception as e:
            raise Exception(traceback.format_exc())


class ServiceList(Lister):
    """List services and their sub-services"""

    def take_action(self, parsed_args):
        try:
            inventory = Inventory.load()

            data = []
            service_subsvcs = inventory.get_service_sub_services()
            if service_subsvcs:
                for (servicename, sub_svcname) in service_subsvcs.items():
                    data.append((servicename, sub_svcname))
            else:
                data.append(('', ''))
            return ((u._('Service'), u._('Sub-Services')), sorted(data))
        except CommandError as e:
            raise e
        except Exception as e:
            raise Exception(traceback.format_exc())
