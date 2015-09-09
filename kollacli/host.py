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
import argparse
import getpass
import logging
import traceback

from kollacli.ansible.inventory import Inventory
from kollacli.exceptions import CommandError
from kollacli.utils import get_setup_user

from cliff.command import Command
from cliff.lister import Lister


def _host_not_found(log, hostname):
    raise CommandError(
        'ERROR: Host (%s) not found. ' % hostname +
        'Please add it with "host add"')


class HostAdd(Command):
    """Add host to open-stack-kolla"""
    log = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super(HostAdd, self).get_parser(prog_name)
        parser.add_argument('hostname', metavar='<hostname>',
                            help='host name or ip address')
        return parser

    def take_action(self, parsed_args):
        try:
            hostname = parsed_args.hostname.strip()

            inventory = Inventory.load()
            inventory.add_host(hostname)
            Inventory.save(inventory)
        except CommandError as e:
            raise e
        except Exception as e:
            raise Exception(traceback.format_exc())


class HostRemove(Command):
    """Remove host from openstack-kolla"""

    log = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super(HostRemove, self).get_parser(prog_name)
        parser.add_argument('hostname', metavar='<hostname>', help='host name')
        return parser

    def take_action(self, parsed_args):
        try:
            hostname = parsed_args.hostname.strip()
            inventory = Inventory.load()
            inventory.remove_host(hostname)
            Inventory.save(inventory)
        except CommandError as e:
            raise e
        except Exception as e:
            raise Exception(traceback.format_exc())


class HostList(Lister):
    """List hosts and their groups

    If a hostname is provided, only list information about that host.
    """

    log = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super(HostList, self).get_parser(prog_name)
        parser.add_argument('hostname', nargs='?', metavar='[hostname]',
                            help='hostname')
        return parser

    def take_action(self, parsed_args):
        try:
            hostname = None
            if parsed_args.hostname:
                hostname = parsed_args.hostname.strip()

            inventory = Inventory.load()

            if hostname:
                host = inventory.get_host(hostname)
                if not host:
                    _host_not_found(self.log, hostname)

            data = []
            host_groups = inventory.get_host_groups()
            if host_groups:
                if hostname:
                    data.append((hostname, host_groups[hostname]))
                else:
                    for (hostname, groupnames) in host_groups.items():
                        data.append((hostname, groupnames))
            else:
                data.append(('', ''))
            return (('Host', 'Groups'), sorted(data))
        except CommandError as e:
            raise e
        except Exception as e:
            raise Exception(traceback.format_exc())


class HostCheck(Command):
    """Check if openstack-kollacli is setup"""

    log = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super(HostCheck, self).get_parser(prog_name)
        parser.add_argument('hostname', metavar='<hostname>', help='hostname')
        return parser

    def take_action(self, parsed_args):
        try:
            self.log.info('check currently disabled, in work')
#            hostname = parsed_args.hostname.strip()
#            inventory = Inventory.load()
#            host = inventory.get_host(hostname)
#            if not host:
#                _host_not_found(self.log, hostname)
#
#            host.check()
        except CommandError as e:
            raise e
        except Exception as e:
            raise Exception(traceback.format_exc())


class HostSetup(Command):
    """Setup openstack-kollacli on host"""

    log = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super(HostSetup, self).get_parser(prog_name)
        parser.add_argument('hostname', metavar='<hostname>', help='hostname')
        parser.add_argument('--insecure', nargs='?', help=argparse.SUPPRESS)
        return parser

    def take_action(self, parsed_args):
        try:
            hostname = parsed_args.hostname.strip()
            setup_user = get_setup_user()
            inventory = Inventory.load()
            host = inventory.get_host(hostname)
            if not host:
                _host_not_found(self.log, hostname)
                return False

            if parsed_args.insecure:
                password = parsed_args.insecure.strip()
            else:
                password = getpass.getpass('%s password for %s: ' %
                                           (setup_user, hostname))

            host.setup(password)
        except CommandError as e:
            raise e
        except Exception as e:
            raise Exception(traceback.format_exc())
