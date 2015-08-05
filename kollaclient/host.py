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

from kollaclient.i18n import _
from kollaclient.objects.hosts import Host
from kollaclient.objects.hosts import Hosts
from kollaclient.objects.zones import Zones

from cliff.command import Command
from cliff.lister import Lister


def _host_not_found(log, hostname):
    log.info('Host (%s) not found. ' % hostname +
             'Please add it with "Host add"')


def _zone_not_found(log, zonename):
    log.info('Zone (%s) not found. ' % zonename +
             'Please add it with "Zone add"')


class HostAdd(Command):
    """Add host to open-stack-kolla

    If host already exists, just update the network address.
    """

    log = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super(HostAdd, self).get_parser(prog_name)
        parser.add_argument('hostname', metavar='<hostname>', help='hostname')
        parser.add_argument('networkaddress', metavar='networkaddress',
                            help='Network address')
        return parser

    def take_action(self, parsed_args):
        hostname = parsed_args.hostname.strip()
        net_addr = parsed_args.networkaddress.strip()

        hosts = Hosts()
        host = Host(hostname, net_addr)
        hosts.add_host(host)
        hosts.save()


class HostRemove(Command):
    """Remove host from openstack-kolla"""

    log = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super(HostRemove, self).get_parser(prog_name)
        parser.add_argument('hostname', metavar='<hostname>', help='hostname')
        return parser

    def take_action(self, parsed_args):
        hostname = parsed_args.hostname.strip()
        hosts = Hosts()
        hosts.remove_host(hostname)
        hosts.save()


class HostList(Lister):
    """List all hosts"""

    log = logging.getLogger(__name__)

    def take_action(self, parsed_args):
        hosts = Hosts().get_all()
        data = []
        if hosts:
            for host in hosts:
                data.append((host.hostname, host.net_addr, host.zone))
        else:
            data.append(('', '', ''))
        return (('Host Name', 'Address', 'Zone'), data)


class HostSetzone(Command):
    """Add a host to a zone"""

    log = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super(HostSetzone, self).get_parser(prog_name)
        parser.add_argument('hostname', metavar='<hostname>', help='host name')
        parser.add_argument('zone', metavar='[zone]', help='zone name')
        return parser

    def take_action(self, parsed_args):
        hostname = parsed_args.hostname.strip()
        zonename = parsed_args.zone.strip()

        if zonename not in Zones().get_all():
            _zone_not_found(self.log, zonename)
            return False

        hosts = Hosts()
        host = hosts.get_host(hostname)
        if not host:
            _host_not_found(self.log, hostname)
            return False

        host.zone = zonename
        hosts.save()


class HostClearzone(Command):
    """Clear the zone from a host"""

    log = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super(HostClearzone, self).get_parser(prog_name)
        parser.add_argument('hostname', metavar='<hostname>', help='host name')
        return parser

    def take_action(self, parsed_args):
        hostname = parsed_args.hostname.strip()

        hosts = Hosts()
        host = hosts.get_host(hostname)
        if not host:
            _host_not_found(self.log, hostname)
            return False

        host.zone = ''
        hosts.save()


class HostAddservice(Command):
    """add service to a host"""

    log = logging.getLogger(__name__)

    def take_action(self, parsed_args):
        self.log.info(_('host addservice'))
        self.app.stdout.write(parsed_args)


class HostRemoveservice(Command):
    """Remove service from a host"""

    log = logging.getLogger(__name__)

    def take_action(self, parsed_args):
        self.log.info(_('host removeservice'))
        self.app.stdout.write(parsed_args)


class HostCheck(Command):
    """Check if openstack-kolla is installed"""

    log = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super(HostCheck, self).get_parser(prog_name)
        parser.add_argument('hostname', metavar='<hostname>', help='hostname')
        return parser

    def take_action(self, parsed_args):
        hostname = parsed_args.hostname.strip()

        host = Hosts().get_host(hostname)
        if not host:
            _host_not_found(self.log, hostname)
            return False

        host.check()


class HostInstall(Command):
    """Install openstack-kolla on host"""

    log = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super(HostInstall, self).get_parser(prog_name)
        parser.add_argument('hostname', metavar='<hostname>', help='hostname')
        parser.add_argument('--insecure', nargs='?', help=argparse.SUPPRESS)
        return parser

    def take_action(self, parsed_args):
        hostname = parsed_args.hostname.strip()
        host = Hosts().get_host(hostname)
        if not host:
            _host_not_found(self.log, hostname)
            return False

        if parsed_args.insecure:
            password = parsed_args.insecure.strip()
        else:
            password = getpass.getpass('Root password of %s: ' % hostname)

        host.install(password)
