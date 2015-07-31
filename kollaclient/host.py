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
import logging
import getpass
import argparse
import traceback

from paramiko import AuthenticationException

from kollaclient.i18n import _
from kollaclient.sshutils import ssh_check_host
from kollaclient.sshutils import ssh_check_keys
from kollaclient.sshutils import ssh_install_host
from kollaclient.sshutils import ssh_keygen
from kollaclient.utils import load_etc_yaml
from kollaclient.utils import save_etc_yaml

from cliff.command import Command

HOSTS_YML_FNAME = 'hosts.yml'
ZONES_YML_FNAME = 'zone.yml'


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
        hostname = parsed_args.hostname.rstrip()
        netAddr = parsed_args.networkaddress.rstrip()

        contents = load_etc_yaml(HOSTS_YML_FNAME)
        if hostname in contents:
            self.log.debug(_('Skipping, host (%s) already added.'
                             % hostname))
            return

        hostEntry = {hostname: {'Services': '', 'NetworkAddress':
                     netAddr, 'Zone': ''}}
        contents.update(hostEntry)
        save_etc_yaml(HOSTS_YML_FNAME, contents)


class HostRemove(Command):
    """Remove host from openstack-kolla"""

    log = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super(HostRemove, self).get_parser(prog_name)
        parser.add_argument('hostname', metavar='<hostname>', help='hostname')
        return parser

    def take_action(self, parsed_args):
        hostname = parsed_args.hostname.rstrip()
        contents = load_etc_yaml(HOSTS_YML_FNAME)

        if hostname in contents:
            del contents[hostname]
        else:
            self.log.debug('Host (%s) not found. Skipping remove' % hostname)
        save_etc_yaml(HOSTS_YML_FNAME, contents)


class HostList(Command):
    """List all hosts"""

    log = logging.getLogger(__name__)

    def take_action(self, parsed_args):
        contents = load_etc_yaml(HOSTS_YML_FNAME)
        # TODO(bmace) fix output format
        for host, hostdata in contents.items():
            self.log.info(host)
            self.log.info(hostdata)


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

        zones = load_etc_yaml(ZONES_YML_FNAME)
        zone_data = zones[zonename]
        if not zone_data:
            _zone_not_found(self.log, zonename)
            return False

        hosts = load_etc_yaml(HOSTS_YML_FNAME)

        if hostname not in hosts:
            _host_not_found(self.log, hostname)
            return False

        host_data = hosts[hostname]
        host_data['Zone'] = zonename
        hosts[hostname] = host_data
        save_etc_yaml(HOSTS_YML_FNAME, hosts)


class HostClearzone(Command):
    """Clear the zone from a host"""

    log = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super(HostClearzone, self).get_parser(prog_name)
        parser.add_argument('hostname', metavar='<hostname>', help='host name')
        return parser

    def take_action(self, parsed_args):
        hostname = parsed_args.hostname.strip()

        hosts = load_etc_yaml(HOSTS_YML_FNAME)
        if hostname not in hosts:
            _host_not_found(self.log, hostname)
            return False

        host_data = hosts[hostname]
        host_data['Zone'] = ''
        hosts[hostname] = host_data
        save_etc_yaml(HOSTS_YML_FNAME, hosts)


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
        hostname = parsed_args.hostname.rstrip()
        contents = load_etc_yaml(HOSTS_YML_FNAME)
        if hostname not in contents:
            _host_not_found(self.log, hostname)
            return False

        sshKeysExist = ssh_check_keys()
        if not sshKeysExist:
            try:
                ssh_keygen()
            except Exception as e:
                self.log.error('Error generating ssh keys: %s' % str(e))
                return False

        host_data = contents[hostname]
        netAddr = host_data['NetworkAddress']

        try:
            self.log.info('Starting host (%s) check at address (%s)' %
                          (hostname, netAddr))
            ssh_check_host(netAddr)
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
        contents = load_etc_yaml(HOSTS_YML_FNAME)
        if hostname not in contents:
            _host_not_found(self.log, hostname)
            return False

        sshKeysExist = ssh_check_keys()
        if not sshKeysExist:
            try:
                ssh_keygen()
            except Exception as e:
                self.log.error('Error generating ssh keys: %s' % str(e))
                return False

        host_data = contents[hostname]
        netAddr = host_data['NetworkAddress']

        # Don't bother doing all the install stuff if the check looks ok
        try:
            ssh_check_host(netAddr)
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
                          (hostname, netAddr))
            ssh_install_host(netAddr, password)
            self.log.info('Host (%s) install succeeded' % hostname)
        except Exception as e:
            self.log.info('Host (%s) install failed (%s)'
                          % (hostname, str(e)))
