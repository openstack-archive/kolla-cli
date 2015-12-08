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
import os
import traceback
import yaml

import kollacli.i18n as u

from kollacli.common.ansible.actions import destroy_hosts
from kollacli.common.inventory import Inventory
from kollacli.common.utils import convert_to_unicode
from kollacli.common.utils import get_setup_user
from kollacli.exceptions import CommandError

from cliff.command import Command
from cliff.lister import Lister

LOG = logging.getLogger(__name__)


def _host_not_found(hostname):
    raise CommandError(
        u._('Host ({host}) not found. Please add it with "host add".')
        .format(host=hostname))


class HostAdd(Command):
    """Add host to open-stack-kolla"""

    def get_parser(self, prog_name):
        parser = super(HostAdd, self).get_parser(prog_name)
        parser.add_argument('hostname', metavar='<hostname>',
                            help=u._('Host name or ip address'))
        return parser

    def take_action(self, parsed_args):
        try:
            hostname = parsed_args.hostname.strip()
            hostname = convert_to_unicode(hostname)

            inventory = Inventory.load()
            inventory.add_host(hostname)
            Inventory.save(inventory)
        except CommandError as e:
            raise e
        except Exception as e:
            raise Exception(traceback.format_exc())


class HostDestroy(Command):
    """Destroy

    Stops and removes all kolla related docker containers on either the
    specified host or if no host is specified, on all hosts.
    """

    def get_parser(self, prog_name):
        parser = super(HostDestroy, self).get_parser(prog_name)
        parser.add_argument('hostname', metavar='<hostname | all>',
                            help=u._('Host name or ip address or "all"'))
        parser.add_argument('--stop', action='store_true',
                            help=u._('Stop rather than kill'))
        parser.add_argument('--includedata', action='store_true',
                            help=u._('Destroy data containers'))
        return parser

    def take_action(self, parsed_args):
        try:
            hostname = ''
            hostname = parsed_args.hostname.strip()
            hostname = convert_to_unicode(hostname)

            destroy_type = 'kill'
            if parsed_args.stop:
                destroy_type = 'stop'
            include_data = False
            if parsed_args.includedata:
                include_data = True

            verbose_level = self.app.options.verbose_level

            destroy_hosts(hostname, destroy_type, verbose_level, include_data)

        except CommandError as e:
            raise e
        except Exception as e:
            raise Exception(traceback.format_exc())


class HostRemove(Command):
    """Remove host from openstack-kolla"""

    def get_parser(self, prog_name):
        parser = super(HostRemove, self).get_parser(prog_name)
        parser.add_argument('hostname', metavar='<hostname>',
                            help=u._('Host name'))
        return parser

    def take_action(self, parsed_args):
        try:
            hostname = parsed_args.hostname.strip()
            hostname = convert_to_unicode(hostname)
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

    def get_parser(self, prog_name):
        parser = super(HostList, self).get_parser(prog_name)
        parser.add_argument('hostname', nargs='?', metavar='[hostname]',
                            help=u._('Host name'))
        return parser

    def take_action(self, parsed_args):
        try:
            hostname = None
            if parsed_args.hostname:
                hostname = parsed_args.hostname.strip()
                hostname = convert_to_unicode(hostname)

            inventory = Inventory.load()

            if hostname:
                host = inventory.get_host(hostname)
                if not host:
                    _host_not_found(hostname)

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
            return ((u._('Host'), u._('Groups')), sorted(data))
        except CommandError as e:
            raise e
        except Exception as e:
            raise Exception(traceback.format_exc())


class HostCheck(Command):
    """Check if openstack-kollacli is setup"""

    def get_parser(self, prog_name):
        parser = super(HostCheck, self).get_parser(prog_name)
        parser.add_argument('hostname', metavar='<hostname>',
                            help=u._('Host name'))
        return parser

    def take_action(self, parsed_args):
        try:
            hostname = parsed_args.hostname.strip()
            hostname = convert_to_unicode(hostname)
            inventory = Inventory.load()
            if not inventory.get_host(hostname):
                _host_not_found(hostname)

            inventory.check_host(hostname)
        except CommandError as e:
            raise e
        except Exception as e:
            raise Exception(traceback.format_exc())


class HostSetup(Command):
    """Setup openstack-kollacli on host"""

    def get_parser(self, prog_name):
        parser = super(HostSetup, self).get_parser(prog_name)
        parser.add_argument('hostname', nargs='?',
                            metavar='<hostname>', help=u._('Host name'))
        parser.add_argument('--insecure', nargs='?', help=argparse.SUPPRESS)
        parser.add_argument('--file', '-f', nargs='?',
                            metavar='<hosts_info_file>',
                            help=u._('Absolute path to hosts info file '))
        return parser

    def take_action(self, parsed_args):
        try:
            if not parsed_args.hostname and not parsed_args.file:
                raise CommandError(
                    u._('Host name or hosts info file path is required.'))
            if parsed_args.hostname and parsed_args.file:
                raise CommandError(
                    u._('Host name and hosts info file path '
                        'cannot both be present.'))
            inventory = Inventory.load()

            if parsed_args.file:
                # multi-host setup via xml file
                hosts_data = self.get_yml_data(parsed_args.file.strip())
                inventory.setup_hosts(hosts_data)
            else:
                # single host setup
                hostname = parsed_args.hostname.strip()
                hostname = convert_to_unicode(hostname)
                if not inventory.get_host(hostname):
                    _host_not_found(hostname)

                check_ok = inventory.check_host(hostname, True)
                if check_ok:
                    LOG.info(
                        u._LI('Skipping setup of host ({host}) as '
                              'check is ok.').format(host=hostname))
                    return True

                if parsed_args.insecure:
                    password = parsed_args.insecure.strip()
                else:
                    setup_user = get_setup_user()
                    password = getpass.getpass(
                        u._('{user} password for {host}: ')
                        .format(user=setup_user, host=hostname))
                password = convert_to_unicode(password)
                inventory.setup_host(hostname, password)

        except CommandError as e:
            raise e
        except Exception as e:
            raise Exception(traceback.format_exc())

    def get_yml_data(self, yml_path):
        if not os.path.isfile(yml_path):
            raise CommandError(
                u._('No file exists at {path}. An absolute file path is '
                    'required.').format(path=yml_path))

        with open(yml_path, 'r') as hosts_file:
            file_data = hosts_file.read()

        hosts_info = yaml.safe_load(file_data)
        if not hosts_info:
            raise CommandError(u._('{path} is empty.').format(path=yml_path))
        return hosts_info
