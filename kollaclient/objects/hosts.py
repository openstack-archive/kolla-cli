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
import kollaclient.utils as utils

import logging
import traceback

from kollaclient.sshutils import ssh_check_host
from kollaclient.sshutils import ssh_check_keys
from kollaclient.sshutils import ssh_install_host
from kollaclient.sshutils import ssh_keygen

from paramiko import AuthenticationException


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
                self.log.error('Error generating ssh keys: %s' % str(e))
                return False

        try:
            self.log.info('Starting host (%s) check at address (%s)' %
                          (self.hostname, self.net_addr))
            ssh_check_host(self.net_addr)
            self.log.info('Host (%s), check succeeded' % self.hostname)
            return True
        except Exception as e:
            self.log.error('Host (%s), check failed (%s)'
                           % (self.hostname, str(e)))
            return False

    def install(self, password):
        sshKeysExist = ssh_check_keys()
        if not sshKeysExist:
            try:
                ssh_keygen()
            except Exception as e:
                self.log.error('Error generating ssh keys: %s' % str(e))
                return False

        # Don't bother doing all the install stuff if the check looks ok
        try:
            ssh_check_host(self.net_addr)
            self.log.info('Install skipped for host (%s), ' % self.hostname +
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
        try:
            self.log.info('Starting install of host (%s) at address (%s)'
                          % (self.hostname, self.net_addr))
            ssh_install_host(self.net_addr, password)
            self.log.info('Host (%s) install succeeded' % self.hostname)
        except Exception as e:
            self.log.info('Host (%s) install failed (%s)'
                          % (self.hostname, str(e)))


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
