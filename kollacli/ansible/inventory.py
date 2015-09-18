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
from kollacli.utils import get_kollacli_home

ANSIBLE_SSH_USER = 'ansible_ssh_user'
ANSIBLE_CONNECTION = 'ansible_connection'
ANSIBLE_BECOME = 'ansible_become'

INVENTORY_PATH = 'ansible/inventory.json'

COMPUTE_GRP_NAME = 'compute'
CONTROL_GRP_NAME = 'control'
NETWORK_GRP_NAME = 'network'
STORAGE_GRP_NAME = 'storage'
DATABASE_GRP_NAME = 'database'

DEPLOY_GROUPS = [
    COMPUTE_GRP_NAME,
    CONTROL_GRP_NAME,
    NETWORK_GRP_NAME,
    STORAGE_GRP_NAME,
    DATABASE_GRP_NAME,
    ]

SERVICES = {
    'cinder':       ['cinder-api', 'cinder-scheduler', 'cinder-backup',
                     'cinder-volume'],
    'glance':       ['glance-api', 'glance-registry'],
    'haproxy':      [],
    'heat':         ['heat-api', 'heat-api-cfn', 'heat-engine'],
    'horizon':      [],
    'keystone':     [],
    'mariadb':      [],
    'memcached':    [],
    'murano':       ['murano-api', 'murano-engine'],
    'mysqlcluster': ['mysqlcluster-api', 'mysqlcluster-mgmt',
                     'mysqlcluster-ndb'],
    'neutron':      ['neutron-server', 'neutron-agents'],
    'nova':         ['nova-api', 'nova-conductor', 'nova-consoleauth',
                     'nova-novncproxy', 'nova-scheduler'],
    'rabbitmq':     [],
    'swift':        ['swift-proxy-server', 'swift-account-server',
                     'swift-container-server', 'swift-object-server'],
    }

DEFAULT_GROUPS = {
    'cinder':                   CONTROL_GRP_NAME,
    'glance':                   CONTROL_GRP_NAME,
    'haproxy':                  CONTROL_GRP_NAME,
    'heat':                     CONTROL_GRP_NAME,
    'horizon':                  CONTROL_GRP_NAME,
    'keystone':                 CONTROL_GRP_NAME,
    'mariadb':                  CONTROL_GRP_NAME,
    'memcached':                CONTROL_GRP_NAME,
    'murano':                   CONTROL_GRP_NAME,
    'mysqlcluster':             CONTROL_GRP_NAME,
    'neutron':                  NETWORK_GRP_NAME,
    'nova':                     CONTROL_GRP_NAME,
    'rabbitmq':                 CONTROL_GRP_NAME,
    'swift':                    CONTROL_GRP_NAME,
    }

DEFAULT_OVERRIDES = {
    'cinder-backup':            STORAGE_GRP_NAME,
    'cinder-volume':            STORAGE_GRP_NAME,
    'mysqlcluster-ndb':         DATABASE_GRP_NAME,
    'neutron-server':           CONTROL_GRP_NAME,
    'swift-account-server':     STORAGE_GRP_NAME,
    'swift-container-server':   STORAGE_GRP_NAME,
    'swift-object-server':      STORAGE_GRP_NAME,
    }


# these groups cannot be deleted, they are required by kolla
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

    def setup(self, password):
        # TODO(bmace) should run check before doing setup
        # not setup- we need to set up the user / remote ssh keys
        # using root and the available password
        try:
            self.log.info('Starting setup of host (%s)'
                          % self.name)
            ssh_setup_host(self.name, password)
            check_ok = self.check(True)
            if not check_ok:
                raise Exception('Post setup check failed')
            self.log.info('Host (%s) setup succeeded' % self.name)
        except Exception as e:
            raise exceptions.CommandError(
                'ERROR: Host (%s) setup failed : %s'
                % (self.name, e))
        return True

    def check(self, result_only=False):
        kollacli_home = get_kollacli_home()
        command_string = 'sudo -u kolla ansible '
        inventory_string = '-i ' + os.path.join(kollacli_home,
                                                'tools', 'json_generator.py')
        ping_string = ' %s %s' % (self.name, '-m ping')
        cmd = (command_string + inventory_string + ping_string)

        err_flag, output = utils.run_cmd(cmd, False)
        if err_flag:
            if result_only:
                return False
            else:
                raise exceptions.CommandError(
                    'ERROR: Host (%s) check failed : %s'
                    % (self.name, output))
        else:
            if not result_only:
                self.log.info('Host (%s) check succeeded' % self.name)
        return True


class HostGroup(object):
    class_version = 1

    def __init__(self, name):
        self.name = name
        self.hostnames = []
        self.vars = {}
        self.version = self.__class__.class_version

    def upgrade(self):
        pass

    def add_host(self, host):
        if host.name not in self.hostnames:
            self.hostnames.append(host.name)

    def remove_host(self, host):
        if host.name in self.hostnames:
            self.hostnames.remove(host.name)

    def get_hostnames(self):
        return self.hostnames

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
        self._sub_servicenames = []
        self._groupnames = []
        self._vars = {}
        self.version = self.__class__.class_version

    def upgrade(self):
        pass

    def add_groupname(self, groupname):
        if not self.get_sub_servicenames():
            # this service has no sub-services
            if groupname not in self._groupnames:
                self._groupnames.append(groupname)
        else:
            raise CommandError('This service (%s) ' % self.name +
                               'cannot be associated to a '
                               'group. Only its sub-services can be ' +
                               'associated to a group.')

    def remove_groupname(self, groupname):
        if groupname in self._groupnames:
            self._groupnames.remove(groupname)

    def get_groupnames(self):
        return self._groupnames

    def get_sub_servicenames(self):
        return self._sub_servicenames

    def add_sub_servicename(self, sub_servicename):
        if sub_servicename not in self._sub_servicenames:
            self._sub_servicenames.append(sub_servicename)

    def get_vars(self):
        return self._vars.copy()


class SubService(object):
    class_version = 1

    def __init__(self, name):
        self.name = name
        self._groupnames = []
        self._vars = {}
        self.version = self.__class__.class_version

    def upgrade(self):
        pass

    def add_groupname(self, groupname):
        if groupname not in self._groupnames:
            self._groupnames.append(groupname)

    def remove_groupname(self, groupname):
        if groupname in self._groupnames:
            self._groupnames.remove(groupname)

    def get_groupnames(self):
        return self._groupnames

    def get_vars(self):
        return self.vars.copy()


class Inventory(object):
    class_version = 1

    def __init__(self):
        self._groups = {}           # kv = name:object
        self._hosts = {}            # kv = name:object
        self._services = {}         # kv = name:object
        self._sub_services = {}     # kv = name:object
        self.vars = {}
        self.version = self.__class__.class_version
        self.remote_mode = True

        # initialize the inventory to its defaults
        self._create_default_inventory()

    def upgrade(self):
        if self.version == 1:
            """
            # upgrading from v1 to v2
            # insert upgrade handler here...
            #
            # here's an example of renaming 'glance' service to 'glance2'
            groups = self.get_groups()
            for group in groups:
                for service in group.services:
                    if service.name == 'glance':
                        service.name = 'glance2'
                        break
            """

        # update version and save upgraded inventory file
        self.version = self.class_version
        Inventory.save(self)

    @staticmethod
    def load():
        """load the inventory from a pickle file"""
        inventory_path = os.path.join(utils.get_kollacli_etc(), INVENTORY_PATH)
        data = ''
        try:
            if os.path.exists(inventory_path):
                with open(inventory_path, 'rb') as inv_file:
                    data = inv_file.read()

            if data.strip():
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
            raise Exception('ERROR: saving inventory : %s' % e)
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

        # create the default groups
        for groupname in DEPLOY_GROUPS:
            self.add_group(groupname)

        # create the default services/sub_services & their default groups
        for svcname in SERVICES:
            svc = self.create_service(svcname)
            default_grpname = DEFAULT_GROUPS[svcname]
            sub_svcnames = SERVICES[svcname]
            if sub_svcnames:
                for sub_svcname in sub_svcnames:
                    # create a subservice
                    sub_svc = self.create_sub_service(sub_svcname)
                    svc.add_sub_servicename(sub_svcname)
                    if sub_svc.name not in DEFAULT_OVERRIDES:
                        sub_svc.add_groupname(default_grpname)
                    else:
                        sub_svc.add_groupname(DEFAULT_OVERRIDES[sub_svc.name])
            else:
                # this service has no sub-services, so it can be
                # associated to a group.
                svc.add_groupname(default_grpname)

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
        if hostname not in self.get_hostnames():
            # a new host is being added to the inventory
            self._hosts[hostname] = host

        # a host is to be added to an existing group
        elif groupname:
            group = self._groups[groupname]
            if hostname not in group.get_hostnames():
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

        # Group names cannot overlap with service names:
        if groupname in self._services or groupname in self._sub_services:
            raise CommandError('ERROR: Invalid group name. A service name '
                               'cannot be used for a group name.')

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
        groups = []
        if not host:
            groups = self._groups.values()

        else:
            for group in self._groups.values():
                if host.name in group.get_hostnames():
                    groups.append(group)
        return groups

    def get_group_services(self):
        """get groups and their instantiated services

        Instantiated services are those services which can be deployed
        on a host.

        It can either be:
        1. a service that has no sub-services
        2. a sub-service

        return { groupname: [instantiated_servicenames] }
        """

        group_services = {}

        for group in self.get_groups():
            group_services[group.name] = []

        for svc in self.get_services():
            if not svc.get_sub_servicenames():
                for groupname in svc.get_groupnames():
                    group_services[groupname].append(svc.name)
            else:
                for sub_svcname in svc.get_sub_servicenames():
                    sub_svc = self.get_sub_service(sub_svcname)
                    for groupname in sub_svc.get_groupnames():
                        group_services[groupname].append(sub_svc.name)
        return group_services

    def get_group_hosts(self):
        """return { groupname : [hostnames] }"""
        group_hosts = {}
        for group in self.get_groups():
            group_hosts[group.name] = []
            for hostname in group.get_hostnames():
                group_hosts[group.name].append(hostname)
        return group_hosts

    def create_service(self, servicename):
        if servicename not in self._services:
            service = Service(servicename)
            self._services[servicename] = service
        return self._services[servicename]

    def delete_service(self, servicename):
        if servicename in self._services:
            del self._services[servicename]

    def get_services(self):
        return self._services.values()

    def get_service(self, servicename):
        service = None
        try:
            service = self._services[servicename]
        except KeyError:
            pass
        return service

    def add_group_to_service(self, groupname, servicename):
        if servicename in self._services:
            service = self.get_service(servicename)
            service.add_groupname(groupname)
        elif servicename in self._sub_services:
                sub_service = self.get_sub_service(servicename)
                sub_service.add_groupname(groupname)
        else:
            raise CommandError('Service (%s) not found' % servicename)

    def remove_group_from_service(self, groupname, servicename):
        if servicename in self._services:
            service = self.get_service(servicename)
            service.remove_groupname(groupname)
        elif servicename in self._sub_services:
                sub_service = self.get_sub_service(servicename)
                sub_service.remove_groupname(groupname)
        else:
            raise CommandError('Service (%s) not found' % servicename)

    def create_sub_service(self, sub_servicename):
        if sub_servicename not in self._sub_services:
            sub_service = SubService(sub_servicename)
            self._sub_services[sub_servicename] = sub_service
        return self._sub_services[sub_servicename]

    def delete_sub_service(self, sub_servicename):
        if sub_servicename in self._sub_services:
            del self._sub_services[sub_servicename]

    def get_sub_services(self):
        return self._sub_services.values()

    def get_sub_service(self, sub_servicename):
        sub_service = None
        try:
            sub_service = self._sub_services[sub_servicename]
        except KeyError:
            pass
        return sub_service

    def get_service_sub_services(self):
        """get services and their sub_services

        return { servicename: [sub_servicenames] }
        """
        svc_sub_svcs = {}
        for service in self.get_services():
            svc_sub_svcs[service.name] = []
            svc_sub_svcs[service.name].extend(service.get_sub_servicenames())
        return svc_sub_svcs

    def get_service_groups(self):
        """set instantiated services and their groups

        Instantiated services are those services which can be deployed
        on a host.

        It can either be:
        1. a service that has no sub-services
        2. a sub-service

        return { instantiated_servicename: [groupnames] }
        """
        inst_svcs = {}
        for svc in self.get_services():
            if not svc.get_sub_servicenames():
                inst_svcs[svc.name] = []
                inst_svcs[svc.name].extend(svc.get_groupnames())
            else:
                for sub_svcname in svc.get_sub_servicenames():
                    sub_svc = self.get_sub_service(sub_svcname)
                    inst_svcs[sub_svcname] = []
                    inst_svcs[sub_svcname].extend(sub_svc.get_groupnames())
        return inst_svcs

    def set_deploy_mode(self, remote_flag):
        if not remote_flag and len(self._hosts) > 1:
            raise CommandError('Cannot set local deploy mode when multiple ' +
                               'hosts exist')
        self.remote_mode = remote_flag

        for group in self.get_groups():
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

        # add top-level services and what groups they are in
        for service in self.get_services():
            jdict[service.name] = {}
            jdict[service.name]['children'] = service.get_groupnames()

        # add sub-services and their groups
        for sub_svc in self.get_sub_services():
            jdict[sub_svc.name] = {}
            jdict[sub_svc.name]['children'] = sub_svc.get_groupnames()

        # temporarily create group containing all hosts. this is needed for
        # ansible commands that are performed on hosts not yet in groups.
        group = self.add_group('__RESERVED__')
        jdict[group.name] = {}
        jdict[group.name]['hosts'] = self.get_hostnames()
        jdict[group.name]['vars'] = group.get_vars()
        self.remove_group(group.name)

        # process hosts vars
        jdict['_meta'] = {}
        jdict['_meta']['hostvars'] = {}
        for host in self.get_hosts():
            jdict['_meta']['hostvars'][host.name] = host.get_vars()
        return json.dumps(jdict, indent=2)
