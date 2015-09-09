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
import json
import jsonpickle
import logging
import os
import shutil
import traceback

from tempfile import mkstemp

from kollacli import exceptions
from kollacli import utils

from kollacli.exceptions import CommandError
from kollacli.sshutils import ssh_setup_host

ANSIBLE_SSH_USER = 'ansible_ssh_user'
ANSIBLE_CONNECTION = 'ansible_connection'
ANSIBLE_BECOME = 'ansible_become'

INVENTORY_PATH = 'ansible/inventory.json'

COMPUTE_GRP_NAME = 'compute'
CONTROL_GRP_NAME = 'control'
NETWORK_GRP_NAME = 'network'
STORAGE_GRP_NAME = 'storage'

DEPLOY_GROUPS = [
    COMPUTE_GRP_NAME,
    CONTROL_GRP_NAME,
    NETWORK_GRP_NAME,
    STORAGE_GRP_NAME,
    ]

SERVICE_GROUPS = {
    'cinder-ctl':   ['cinder-api', 'cinder-scheduler'],
    'cinder-data':  ['cinder-backup', 'cinder-volume'],
    'glance':       ['glance-api', 'glance-registry'],
    'haproxy':      [],
    'heat':         ['heat-api', 'heat-api-cfn', 'heat-engine'],
    'horizon':      [],
    'keystone':     [],
    'mariadb':      [],
    'memcached':    [],
    'ndbcluster':   ['ndb-data', 'ndb-mgmt', 'ndb-mysql'],
    'neutron':      ['neutron-server', 'neutron-agents'],
    'nova':         ['nova-api', 'nova-conductor', 'nova-consoleauth',
                     'nova-novncproxy', 'nova-scheduler'],
    'rabbitmq':      [],
    'swift':        ['swift-proxy-server', 'swift-account-server',
                     'swift-container-server', 'swift-object-server'],
    }

DEFAULT_HIERARCHY = {
    CONTROL_GRP_NAME: [
        'glance',
        'heat',
        'horizon',
        'keystone',
        'ndbcluster',
        'nova',
        'memcached',
        'rabbitmq',
        'cinder-ctl',
        ],
    NETWORK_GRP_NAME: [
        'haproxy',
        'neutron',
        ],
    COMPUTE_GRP_NAME: [],
    STORAGE_GRP_NAME: [
        'cinder-data',
        'swift',
        ]
    }

PROTECTED_GROUPS = [COMPUTE_GRP_NAME]


class Host(object):
    class_version = 1
    log = logging.getLogger(__name__)

    def __init__(self, hostname):
        self.name = hostname
        self.alias = ''
        self.is_mgmt = False
        self.hypervisor = ''
        self.vars = {}
        self.version = self.__class__.class_version

    def get_vars(self):
        return self.vars.copy()

    def set_var(self, name, value):
        self.vars[name] = value

    def upgrade(self):
        pass

# TODO(bmace) needs to be updated to use ansible
# def check(self):
# sshKeysExist = ssh_check_keys()
# if not sshKeysExist:
# try:
# ssh_keygen()
# except Exception as e:
# raise exceptions.CommandError(
# 'ERROR: ssh key generation failed on local host : %s'
# % str(e))
# try:
# self.log.info('Starting check of host (%s)' % self.name)
# ssh_check_host(self.name)
# self.log.info('Host (%s), check succeeded' % self.name)
# except CommandError as e:
# raise e
# except Exception as e:
# raise Exception(
# 'ERROR: Host (%s), check failed. Reason : %s'
# % (self.name, str(e)))
# return True

    def setup(self, password):
        # self._setup_keys()
        # check if already setup
        # if self._is_setup():
        # self.log.info('Setup skipped for host (%s), ' % self.name +
        # 'kolla already setup')
        # return True

        # not setup- we need to set up the user / remote ssh keys
        # using root and the available password
        try:
            self.log.info('Starting setup of host (%s)'
                          % self.name)
            ssh_setup_host(self.name, password)
            self.log.info('Host (%s) setup succeeded' % self.name)
        except Exception as e:
            raise exceptions.CommandError(
                'ERROR: Host (%s) setup failed : %s'
                % (self.name, str(e)))
        return True

# TODO(bmace) change to use ansible for check
# def _is_setup(self):
# is_setup = False
# try:
# ssh_check_host(self.name)
# is_setup = True
# except Exception as e:
# self.log.debug('%s' % str(e))
# pass
# return is_setup


class HostGroup(object):
    class_version = 1

    def __init__(self, name):
        self.name = name
        self.services = []
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

    def remove_host(self, host):
        if host.name in self._hosts:
            del self._hosts[host.name]

    def add_service(self, servicename):
        service = Service(servicename)
        if service not in self.services:
            self.services.append(service)
        return service

    def remove_service(self, servicename):
        for service in self.services:
            if servicename == service.name:
                self.services.remove(service)

    def get_hosts(self):
        return self._hosts.values()

    def get_hostnames(self):
        return self._hosts.keys()

    def get_servicenames(self):
        names = []
        for service in self.services:
            names.append(service.name)
        return names

    def get_vars(self):
        return self.vars.copy()

    def set_var(self, name, value):
        self.vars[name] = value

    def clear_var(self, name):
        if name in self.vars:
            del self.vars[name]

    def set_remote(self, remote_flag):
        self.set_var(ANSIBLE_BECOME, 'yes')
        if remote_flag:
            # set the ssh info for all the servers in the group
            self.set_var(ANSIBLE_SSH_USER, utils.get_admin_user())
            self.clear_var(ANSIBLE_CONNECTION)
        else:
            # remove ssh info, add local connection type
            self.set_var(ANSIBLE_CONNECTION, 'local')
            self.clear_var(ANSIBLE_SSH_USER)


class Service(object):
    class_version = 1

    def __init__(self, name):
        self.name = name
        self._hosts = {}   # kv = name:object
        self.containers = SERVICE_GROUPS[name]
        self.vars = {}
        self.version = self.__class__.class_version

    def upgrade(self):
        pass

    def get_hostnames(self):
        return self._hosts.keys()

    def get_vars(self):
        return self.vars.copy()


class Inventory(object):
    class_version = 1

    def __init__(self):
        self._groups = {}  # kv = name:object
        self._hosts = {}   # kv = name:object
        self.vars = {}
        self.version = self.__class__.class_version
        self.remote_mode = True

        # initialize the inventory to its defaults
        self._create_default_inventory()

    def upgrade(self):
        pass

    @staticmethod
    def load():
        """load the inventory from a pickle file"""
        inventory_path = os.path.join(utils.get_kollacli_etc(), INVENTORY_PATH)
        data = ''
        try:
            if os.path.exists(inventory_path):
                with open(inventory_path, 'rb') as inv_file:
                    data = inv_file.read()

            if data:
                inventory = jsonpickle.decode(data)

                # upgrade version handling
                if inventory.version != inventory.class_version:
                    inventory.upgrade()
            else:
                inventory = Inventory()
        except Exception:
            raise Exception('ERROR: loading inventory : %s'
                            % traceback.format_exc())
        return inventory

    @staticmethod
    def save(inventory):
        """Save the inventory in a pickle file"""
        inventory_path = os.path.join(utils.get_kollacli_etc(), INVENTORY_PATH)
        try:
            # the file handle returned from mkstemp must be closed or else
            # if this is called many times you will have an unpleasant
            # file handle leak
            tmp_filehandle, tmp_path = mkstemp()

            # multiple trips thru json to render a readable inventory file
            data = jsonpickle.encode(inventory)
            data_str = json.loads(data)
            pretty_data = json.dumps(data_str, indent=4)
            with open(tmp_path, 'w') as tmp_file:
                tmp_file.write(pretty_data)
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
        for (group_name, service_names) in DEFAULT_HIERARCHY.items():
            group = self.add_group(group_name)

            # add services
            for service_name in service_names:
                group.add_service(service_name)
            self._groups[group_name] = group

    def get_hosts(self):
        return self._hosts.values()

    def get_hostnames(self):
        return self._hosts.keys()

    def get_host_groups(self):
        """return { hostname : groupnames }"""

        host_groups = {}
        for host in self._hosts.values():
            host_groups[host.name] = []
            groups = self.get_groups(host)
            for group in groups:
                host_groups[host.name].append(group.name)
        return host_groups

    def get_host(self, hostname):
        host = None
        if hostname in self._hosts:
            host = self._hosts[hostname]
        return host

    def add_host(self, hostname, groupname=None):
        """add host

        if groupname is none, create a new host
        if group name is not none, add host to group
        """
        if groupname and groupname not in self._groups:
            raise CommandError('Group name (%s) does not exist'
                               % groupname)

        if groupname and hostname not in self._hosts:
            raise CommandError('Host name (%s) does not exist'
                               % hostname)

        if not groupname and not self.remote_mode and len(self._hosts) >= 1:
            raise CommandError('Cannot have more than one host when in ' +
                               'local deploy mode')

        # create new host if it doesn't exist
        host = Host(hostname)
        if not groupname:
            self._hosts[hostname] = host
        else:
            group = self._groups[groupname]
            group.add_host(host)

    def remove_host(self, hostname, groupname=None):
        """remove host

        if groupname is none, delete host
        if group name is not none, remove host from group
        """
        if groupname and groupname not in self._groups:
            raise CommandError('Group name (%s) does not exist'
                               % groupname)

        if hostname not in self._hosts:
            return

        host = self._hosts[hostname]
        groups = self.get_groups(host)
        for group in groups:
            if not groupname or groupname == group.name:
                group.remove_host(host)

        if not groupname:
            del self._hosts[hostname]

    def add_group(self, groupname):
        if groupname not in self._groups:
            self._groups[groupname] = HostGroup(groupname)

        group = self._groups[groupname]

        group.set_remote(self.remote_mode)

        return group

    def remove_group(self, groupname):
        if groupname in PROTECTED_GROUPS:
            raise CommandError('Cannot remove %s group. ' % groupname +
                               'It is required by kolla.')
        if groupname in self._groups:
            del self._groups[groupname]

    def get_groups(self, host=None):
        """return all groups containing host

        if hosts is none, return all groups in inventory
        """
        if not host:
            return self._groups.values()

        groups = []
        for group in self._groups.values():
            if host.name in group.get_hostnames():
                groups.append(group)
        return groups

    def get_group_services(self):
        """return { groupname : [servicenames] }"""
        group_services = {}
        for group in self._groups.values():
            group_services[group.name] = []
            for service in group.services:
                group_services[group.name].append(service.name)
        return group_services

    def get_group_hosts(self):
        """return { groupname : [hostnames] }"""
        group_hosts = {}
        for group in self._groups.values():
            group_hosts[group.name] = []
            for host in group.get_hosts():
                group_hosts[group.name].append(host.name)
        return group_hosts

    def add_service(self, servicename, groupname):
        if groupname not in self._groups:
            raise CommandError('Group name (%s) does not exist'
                               % groupname)

        if servicename not in SERVICE_GROUPS.keys():
            raise CommandError('Service name (%s) does not exist'
                               % servicename)

        group_services = self.get_group_services()
        if servicename not in group_services[groupname]:
            group = self._groups[groupname]
            group.services.append(Service(servicename))

    def remove_service(self, servicename, groupname):
        if groupname not in self._groups:
            raise CommandError('Group name (%s) does not exist'
                               % groupname)

        if servicename not in SERVICE_GROUPS.keys():
            raise CommandError('Service name (%s) does not exist'
                               % servicename)

        group = self._groups[groupname]
        group.remove_service(servicename)

    def get_service_groups(self):
        """return { servicename : groupnames }"""
        service_groups = {}
        group_services = self.get_group_services()
        for servicename in SERVICE_GROUPS.keys():
            service_groups[servicename] = []
            for (groupname, servicenames) in group_services.items():
                if servicename in servicenames:
                    service_groups[servicename].append(groupname)
        return service_groups

    def set_deploy_mode(self, remote_flag):
        if not remote_flag and len(self._hosts) > 1:
            raise CommandError('Cannot set local deploy mode when multiple ' +
                               'hosts exist')
        self.remote_mode = remote_flag

        for group in self._groups.values():
            group.set_remote(remote_flag)

    def get_ansible_json(self):
        """generate json inventory for ansible

        typical ansible json format:
        {
        'group': {
            'hosts': [
                '192.168.28.71',
                '192.168.28.72'
            ],
            'vars': {
                'ansible_ssh_user': 'johndoe',
                'ansible_ssh_private_key_file': '~/.ssh/mykey',
                'example_variable': 'value'
            }
            'children': [ 'marietta', '5points' ]
        },
        '_meta': {
            'hostvars': {
                '192.168.28.71': {
                    'host_specific_var': 'bar'
                },
                '192.168.28.72': {
                    'host_specific_var': 'foo'
                }
            }
        }
    }
    """
        jdict = {}

        # add hostgroups
        for group in self.get_groups():
            jdict[group.name] = {}
            jdict[group.name]['hosts'] = group.get_hostnames()
            jdict[group.name]['children'] = []
            jdict[group.name]['vars'] = group.get_vars()

        # add services
        services = []
        for group in self.get_groups():
            for service in group.services:
                if service.name not in jdict:
                    services.append(service)
                    jdict[service.name] = {}
                    jdict[service.name]['vars'] = service.get_vars()
                    jdict[service.name]['children'] = []
                if group.name not in jdict[service.name]['children']:
                    jdict[service.name]['children'].append(group.name)

        # add containers
        for service in services:
            for containername in service.containers:
                jdict[containername] = {}
                jdict[containername]['children'] = [service.name]
                jdict[containername]['vars'] = {}

        # process hosts vars
        jdict['_meta'] = {}
        jdict['_meta']['hostvars'] = {}
        for host in self.get_hosts():
            jdict['_meta']['hostvars'][host.name] = host.get_vars()
        return json.dumps(jdict, indent=2)
