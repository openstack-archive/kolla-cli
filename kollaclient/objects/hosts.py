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
import traceback

from paramiko import AuthenticationException

from kollaclient import exceptions
from kollaclient import utils

from kollaclient.sshutils import ssh_check_host
from kollaclient.sshutils import ssh_check_keys
from kollaclient.sshutils import ssh_install_host
from kollaclient.sshutils import ssh_keygen
from kollaclient.sshutils import ssh_uninstall_host


class Host(object):
    hostname = ''
    net_addr = ''
    zone = ''
    services = []
    log = logging.getLogger(__name__)

    def __init__(self, hostname, net_addr=''):
        self.hostname = hostname
        self.net_addr = net_addr

    def check(self):
        sshKeysExist = ssh_check_keys()
        if not sshKeysExist:
            try:
                ssh_keygen()
            except Exception as e:
                raise exceptions.CommandError(
                    'ERROR: ssh key generation failed on local host : %s'
                    % e)

        try:
            self.log.info('Starting host (%s) check at address (%s)' %
                          (self.hostname, self.net_addr))
            ssh_check_host(self.net_addr)
            self.log.info('Host (%s), check succeeded' % self.hostname)

        except AuthenticationException as e:
            raise exceptions.CommandError(
                'ERROR: Host (%s), check failed, kolla is not installed'
                % self.hostname)
        except Exception as e:
            raise Exception(
                'ERROR: Host (%s), unexpected exception : %s'
                % (self.hostname, e))
        return True

    def install(self, password):
        self._setup_keys()

        # check if already installed
        if self._is_installed():
            self.log.info('Install skipped for host (%s), ' % self.hostname +
                          'kolla already installed')
            return True

        # not installed- we need to set up the user / remote ssh keys
        # using root and the available password
        try:
            self.log.info('Starting install of host (%s) at address (%s)'
                          % (self.hostname, self.net_addr))
            ssh_install_host(self.net_addr, password)
            self.log.info('Host (%s) install succeeded' % self.hostname)
        except Exception as e:
            raise exceptions.CommandError(
                'ERROR: Host (%s) install failed : %s'
                % (self.hostname, e))
        return True

    def uninstall(self):
        self._setup_keys()

        # check if already uninstalled
        if not self._is_installed():
            self.log.info('Uninstall skipped for host (%s), ' % self.hostname +
                          'kolla already uninstalled')
            return True

        try:
            self.log.info('Starting uninstall of host (%s) at address (%s)'
                          % (self.hostname, self.net_addr))
            ssh_uninstall_host(self.net_addr)
            self.log.info('Host (%s) uninstall succeeded' % self.hostname)
        except Exception as e:
            raise exceptions.CommandError(
                'ERROR: Host (%s) uninstall failed : %s'
                % (self.hostname, e))
        return True

    def _setup_keys(self):
        sshKeysExist = ssh_check_keys()
        if not sshKeysExist:
            try:
                ssh_keygen()
            except Exception as e:
                raise exceptions.CommandError(
                    'ERROR: Error generating ssh keys on local host : %s'
                    % e)

    def _is_installed(self):
        is_installed = False
        try:
            ssh_check_host(self.net_addr)
            is_installed = True

        except AuthenticationException:
            # ssh check failed
            pass

        except Exception:
            raise Exception('ERROR: Unexpected exception: %s'
                            % traceback.format_exc())
        return is_installed


class Hosts(object):
    _hosts = {}

    def __init__(self):
        yml = utils.load_etc_yaml('hosts.yml')
        for (hostname, info) in yml.items():
            host = Host(hostname)
            if 'NetworkAddress' in info:
                host.net_addr = info['NetworkAddress']
            if 'Zone' in info:
                host.zone = info['Zone']
            if 'Services' in info:
                service_list = info['Services']
                if service_list:
                    host.services = service_list.split(',')
            self._hosts[hostname] = host

    def get_all(self):
        return self._hosts.values()

    def get_host(self, hostname):
        host = None
        if hostname in self._hosts:
            host = self._hosts[hostname]
        return host

    def add_host(self, host):
        if host.hostname not in self._hosts:
            self._hosts[host.hostname] = host
        else:
            # existing host, just update network address
            cur_host = self._hosts[host.hostname]
            cur_host.net_addr = host.net_addr

    def remove_host(self, hostname):
        if hostname in self._hosts:
            del self._hosts[hostname]

    def save(self):
        """save hosts info"""
        info = {}
        for host in self._hosts.values():
            info[host.hostname] = {}
            info[host.hostname]['NetworkAddress'] = host.net_addr
            info[host.hostname]['Zone'] = host.zone
            info[host.hostname]['Services'] = []
            for service in host.services:
                info[host.hostname]['Services'].append(service)

        utils.save_etc_yaml('hosts.yml', info)
