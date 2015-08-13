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
import jsonpickle
import logging
import os
import shutil

from tempfile import mkstemp

from kollacli import exceptions
from kollacli import utils

from kollacli.sshutils import ssh_check_host
from kollacli.sshutils import ssh_check_keys
from kollacli.sshutils import ssh_install_host
from kollacli.sshutils import ssh_keygen
from kollacli.sshutils import ssh_uninstall_host

from kollacli.exceptions import CommandError

INVENTORY_PATH = 'ansible/inventory/inventory.p'

COMPUTE_GRP_NAME = 'compute'
CONTROL_GRP_NAME = 'control'
NETWORK_GRP_NAME = 'network'

DEPLOY_GROUPS = [COMPUTE_GRP_NAME,
                 CONTROL_GRP_NAME,
                 NETWORK_GRP_NAME,
                 ]

SERVICE_GROUPS = ['mariadb', 'rabbitmq', 'keystone', 'glance',
                  'nova', 'haproxy', 'neutron']

CONTAINER_GROUPS = ['glance-api', 'glance-registry',
                    'nova-api', 'nova-conductor', 'nova-consoleauth',
                    'nova-novncproxy', 'nova-scheduler',
                    'neutron-server', 'neutron-agents']

DEFAULT_HIERARCHY = {
    CONTROL_GRP_NAME: {
        'glance':   ['glance-api', 'glance-registry'],
        'keystone': [],
        'mariadb':  [],
        'nova':     ['nova-api', 'nova-conductor', 'nova-consoleauth',
                     'nova-novncproxy', 'nova-scheduler'],
        'rabbitmq': [],
        },
    NETWORK_GRP_NAME: {
        'haproxy': [],
        'neutron': ['neutron-server', 'neutron-agents'],
        },
    COMPUTE_GRP_NAME: {
        },
    }


class Host(object):
    class_version = 1
    log = logging.getLogger(__name__)

    def __init__(self, hostname):
        self.name = hostname
        self._groups = {}  # kv = groupname:group
        self.alias = ''
        self.is_mgmt = False
        self.hypervisor = ''
        self.vars = {}
        self.version = self.__class__.class_version

    def upgrade(self):
        pass

    def _add_group(self, group):
        if group.name not in self._groups:
            self._groups[group.name] = group

    def _remove_group(self, group):
        if group.name in self._groups:
            del self._groups[group.name]

    def get_groups(self):
        return self._groups.values()

    def check(self):
        sshKeysExist = ssh_check_keys()
        if not sshKeysExist:
            try:
                ssh_keygen()
            except Exception as e:
                raise exceptions.CommandError(
                    'ERROR: ssh key generation failed on local host : %s'
                    % str(e))

        try:
            self.log.info('Starting check of host (%s)' % self.name)
            ssh_check_host(self.name)
            self.log.info('Host (%s), check succeeded' % self.name)

        except Exception as e:
            raise Exception(
                'ERROR: Host (%s), check failed. Reason : %s'
                % (self.name, str(e)))
        return True

    def install(self, password):
        self._setup_keys()

        # check if already installed
        if self._is_installed():
            self.log.info('Install skipped for host (%s), ' % self.name +
                          'kolla already installed')
            return True

        # not installed- we need to set up the user / remote ssh keys
        # using root and the available password
        try:
            self.log.info('Starting install of host (%s)'
                          % self.name)
            ssh_install_host(self.name, password)
            self.log.info('Host (%s) install succeeded' % self.name)
        except Exception as e:
            raise exceptions.CommandError(
                'ERROR: Host (%s) install failed : %s'
                % (self.name, str(e)))
        return True

    def uninstall(self, password):
        self._setup_keys()

        try:
            self.log.info('Starting uninstall of host (%s)' % self.name)
            ssh_uninstall_host(self.name, password)
            self.log.info('Host (%s) uninstall succeeded' % self.name)
        except Exception as e:
            raise exceptions.CommandError(
                'ERROR: Host (%s) uninstall failed : %s'
                % (self.name, str(e)))
        return True

    def _setup_keys(self):
        sshKeysExist = ssh_check_keys()
        if not sshKeysExist:
            try:
                ssh_keygen()
            except Exception as e:
                raise exceptions.CommandError(
                    'ERROR: Error generating ssh keys on local host : %s'
                    % str(e))

    def _is_installed(self):
        is_installed = False
        try:
            ssh_check_host(self.name)
            is_installed = True

        except Exception as e:
            self.log.debug('%s' % str(e))
            pass
        return is_installed


class Group(object):
    class_version = 1

    def __init__(self, name):
        self.name = name
        self.parent = None
        self.children = []
        self._hosts = {}  # kv = hostname:object
        self._version = 1
        self.vars = {}
        self.version = self.__class__.class_version

    def upgrade(self):
        pass

    def add_host(self, host):
        if host.name not in self._hosts:
            self._hosts[host.name] = host
        else:
            host = self._hosts[host.name]
        host._add_group(self)

    def remove_host(self, host):
        if host.name in self._hosts:
            host._remove_group(self)
            del self._hosts[host.name]

    def get_hosts(self):
        return self._hosts.values()


class Inventory(object):
    class_version = 1

    def __init__(self):
        self._groups = {}  # kv = name:object
        self._hosts = {}   # kv = name:object
        self.vars = {}
        self.version = self.__class__.class_version

        # initialize the inventory to its defaults
        self._create_default_inventory()

    def upgrade(self):
        pass

    @staticmethod
    def load():
        """load the inventory from a pickle file"""
        inventory_path = os.path.join(utils.get_client_etc(), INVENTORY_PATH)
        try:
            if os.path.exists(inventory_path):
                with open(inventory_path, 'rb') as inv_file:
                    data = inv_file.read()

                inventory = jsonpickle.decode(data)

                # upgrade version handling
                if inventory.version != inventory.class_version:
                    inventory.upgrade()
            else:
                inventory = Inventory()
        except Exception as e:
            raise Exception('ERROR: loading inventory : %s' % str(e))
        return inventory

    @staticmethod
    def save(inventory):
        """Save the inventory in a pickle file"""
        inventory_path = os.path.join(utils.get_client_etc(), INVENTORY_PATH)
        try:
            # the file handle returned from mkstemp must be closed or else
            # if this is called many times you will have an unpleasant
            # file handle leak
            tmp_filehandle, tmp_path = mkstemp()
            data = jsonpickle.encode(inventory)
            with open(tmp_path, 'w') as tmp_file:
                tmp_file.write(data)
            shutil.copyfile(tmp_path, inventory_path)
            os.remove(tmp_path)
        except Exception as e:
            raise Exception('ERROR: saving inventory : %s' % str(e))
        finally:
            try:
                os.close(tmp_filehandle)
            except Exception:
                pass

            if tmp_filehandle is not None:
                try:
                    os.close(tmp_filehandle)
                except Exception:
                    pass

    def _create_default_inventory(self):
        for (deploy_name, services) in DEFAULT_HIERARCHY.items():
            deploy_group = Group(deploy_name)
            # add service groups
            for (service_name, container_names) in services.items():
                service_group = Group(service_name)
                deploy_group.children.append(service_group)
                service_group.parent = deploy_group
                for container_name in container_names:
                    container_group = Group(container_name)
                    service_group.children.append(container_group)
                    container_group.parent = service_group
            self._groups[deploy_name] = deploy_group

    def get_hosts(self):
        return self._hosts.values()

    def get_host(self, hostname):
        host = None
        if hostname in self._hosts:
            host = self._hosts[hostname]
        return host

    def add_host(self, hostname, groupname):
        if groupname not in self._groups:
            raise CommandError('Group name not valid')

        # create new host if it doesn't exist
        if hostname not in self._hosts:
            host = Host(hostname)
            self._hosts[hostname] = host
        else:
            host = self._hosts[hostname]

        group = self._groups[groupname]
        group.add_host(host)

    def remove_host(self, hostname, groupname=None):
        if hostname in self._hosts:
            host = self._hosts[hostname]
            groups = host.get_groups()
            for group in groups:
                if not groupname or groupname == group.name:
                    host._remove_group(group)

            # if host no longer exists in any group, remove it from inventory
            if not host.get_groups():
                del self._hosts[hostname]
