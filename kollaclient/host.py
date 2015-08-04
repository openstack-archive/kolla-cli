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

from paramiko import AuthenticationException

from kollaclient.i18n import _
from kollaclient.sshutils import ssh_check_host
from kollaclient.sshutils import ssh_check_keys
from kollaclient.sshutils import ssh_install_host
from kollaclient.sshutils import ssh_keygen
from kollaclient.utils import Host
from kollaclient.utils import Hosts
from kollaclient.utils import Zones

from cliff.command import Command
from cliff.lister import Lister


def _host_not_found(log, hostname):
    log.info('Host (%s) not found. ' % hostname +
             'Please add it with "Host add"')


def _zone_not_found(log, zonename):
    log.info('Zone (%s) not found. ' % zonename +
             'Please add it with "Zone add"')


class HostAdd(Command):
    """Add host to open-stack-kolla"""

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
        host = hosts.get_host(hostname)
        if not host:
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

        sshKeysExist = ssh_check_keys()
        if not sshKeysExist:
            try:
                ssh_keygen()
            except Exception as e:
                self.log.error('Error generating ssh keys: %s' % str(e))
                return False

        try:
            self.log.info('Starting host (%s) check at address (%s)' %
                          (hostname, host.net_addr))
            ssh_check_host(host.net_addr)
            self.log.info('Host (%s), check succeeded' % hostname)
            return True
        except Exception as e:
            self.log.error('Host (%s), check failed (%s)' % (hostname, str(e)))
            return False


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
        host = Hosts.get_host(hostname)
        if not host:
            _host_not_found(self.log, hostname)
            return False

        sshKeysExist = ssh_check_keys()
        if not sshKeysExist:
            try:
                ssh_keygen()
            except Exception as e:
                self.log.error('Error generating ssh keys: %s' % str(e))
                return False

        # Don't bother doing all the install stuff if the check looks ok
        try:
            ssh_check_host(host.net_addr)
            self.log.info('Install skipped for host (%s), ' % hostname +
                          'kolla already installed')
            return True

        except AuthenticationException as e:
            # ssh check failed
            pass

        except Exception as e:
            self.log.error('Unexpected exception: %s' % traceback.format_exc())
            raise e

        # sshCheck failed- we need to set up the user / remote ssh keys
        # using root and the available password
        if parsed_args.insecure:
            password = parsed_args.insecure.strip()
        else:
            password = getpass.getpass('Root password of %s: ' % hostname)

        try:
            self.log.info('Starting install of host (%s) at %s)' %
                          (hostname, host.net_addr))
            ssh_install_host(host.net_addr, password)
            self.log.info('Host (%s) install succeeded' % hostname)
        except Exception as e:
            self.log.info('Host (%s) install failed (%s)'
                          % (hostname, str(e)))
