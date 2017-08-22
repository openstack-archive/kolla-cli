# Copyright(c) 2016, Oracle and/or its affiliates.  All Rights Reserved.
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
from copy import copy
import json
import jsonpickle
import logging
import os
import tempfile
import traceback
import uuid

import kollacli.i18n as u

from kollacli.api.exceptions import FailedOperation
from kollacli.api.exceptions import HostError
from kollacli.api.exceptions import InvalidArgument
from kollacli.api.exceptions import InvalidConfiguration
from kollacli.api.exceptions import MissingArgument
from kollacli.api.exceptions import NotInInventory
from kollacli.common.allinone import AllInOne
from kollacli.common.host import Host
from kollacli.common.host_group import HostGroup
from kollacli.common.service import Service
from kollacli.common.sshutils import ssh_setup_host
from kollacli.common.subservice import SubService
from kollacli.common.utils import get_admin_uids
from kollacli.common.utils import get_admin_user
from kollacli.common.utils import get_ansible_command
from kollacli.common.utils import get_group_vars_dir
from kollacli.common.utils import get_host_vars_dir
from kollacli.common.utils import get_kollacli_etc
from kollacli.common.utils import run_cmd
from kollacli.common.utils import sync_read_file
from kollacli.common.utils import sync_write_file

ANSIBLE_SSH_USER = 'ansible_ssh_user'
ANSIBLE_CONNECTION = 'ansible_connection'
ANSIBLE_BECOME = 'ansible_become'

INVENTORY_PATH = 'ansible/inventory.json'

COMPUTE_GRP_NAME = 'compute'

# these groups cannot be deleted, they are required by kolla
PROTECTED_GROUPS = [COMPUTE_GRP_NAME]

LOG = logging.getLogger(__name__)


def remove_temp_inventory(path):
    # type: (str) -> None
    """remove temp inventory file and its parent directory"""
    if path:
        if os.path.exists(path):
            os.remove(path)
        dirpath = os.path.dirname(path)
        if os.path.exists(dirpath):
            os.rmdir(dirpath)


class Inventory(object):
    class_version = 4
    """class version history

    4: (v4.0.1):
        - more sub-services added
    3: (v3.0.1):
        - added aodh, ceph
        - fix to ensure all sub-services have service as parent
    2: (v2.1.1) added ceilometer
    1: (v2.0.1) initial release
    """
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
        # check for new services or subservices in the all-in-one file
        self._upgrade_services()

        if self.version <= 1:
            # upgrade from inventory v1

            # set ceilometer groups to that of heat
            heat = self.get_service('heat')
            ceilometer = self.get_service('ceilometer')
            groups = heat.get_groupnames()
            for group in groups:
                ceilometer.add_groupname(group)

        if self.version <= 3:
            # upgrade from inventory v2 / v3

            # some sub-services may be missing their parent associations.
            # they are now needed in v3 / v4
            for svc in self.get_services():
                for sub_svcname in svc.get_sub_servicenames():
                    sub_svc = self.get_sub_service(sub_svcname)
                    if not sub_svc.get_parent_servicename():
                        sub_svc.set_parent_servicename(svc.name)

        # update the version and save upgraded inventory file
        self.version = self.__class__.class_version
        Inventory.save(self)

    def _upgrade_services(self):
        allinone = AllInOne()
        # add new services
        for servicename, service in allinone.services.items():
            if servicename not in self._services:
                self._services[servicename] = service
        # add new subservices
        for subservicename, subservice in allinone.sub_services.items():
            if subservicename not in self._sub_services:
                self._sub_services[subservicename] = subservice

        # remove obsolete subservices
        for subservicename in copy(self._sub_services).keys():
            if subservicename not in allinone.sub_services:
                self.delete_sub_service(subservicename)
        # remove obsolete services
        for servicename in copy(self._services).keys():
            if servicename not in allinone.services:
                self.delete_service(servicename)

    @staticmethod
    def load():
        """load the inventory from a pickle file"""
        inventory_path = os.path.join(get_kollacli_etc(), INVENTORY_PATH)
        data = ''
        try:
            if os.path.exists(inventory_path):
                data = sync_read_file(inventory_path)

                # The inventory path changed between v1 and v2. Need to change
                # path throughout the inventory. This has to be done before
                # the pickle decode.
                if 'kollacli.common.inventory' not in data:
                    data = data.replace(
                        '"py/object": "kollacli.ansible.inventory.',
                        '"py/object": "kollacli.common.inventory.')

                # The Host, HostGroup, Service and SubService were moved out of
                # inventory and into their own modules
                if 'kollacli.common.service' not in data:
                    data = data.replace(
                        '"py/object": "kollacli.common.inventory.Service"',
                        '"py/object": "kollacli.common.service.Service"')
                    data = data.replace(
                        '"py/object": "kollacli.common.inventory.SubService"',
                        '"py/object": "kollacli.common.subservice.SubService"')
                    data = data.replace(
                        '"py/object": "kollacli.common.inventory.Host"',
                        '"py/object": "kollacli.common.host.Host"')
                    data = data.replace(
                        '"py/object": "kollacli.common.inventory.HostGroup"',
                        '"py/object": "kollacli.common.host_group.HostGroup"')

            if data.strip():
                inventory = jsonpickle.decode(data)

                # upgrade version handling
                if inventory.version != inventory.class_version:
                    inventory.upgrade()
            else:
                inventory = Inventory()
        except Exception:
            raise FailedOperation(
                u._('Loading inventory failed. : {error}')
                .format(error=traceback.format_exc()))
        return inventory

    @staticmethod
    def save(inventory):
        """Save the inventory in a pickle file"""
        inventory_path = os.path.join(get_kollacli_etc(), INVENTORY_PATH)
        try:
            # multiple trips thru json to render a readable inventory file
            data = jsonpickle.encode(inventory)
            data_str = json.loads(data)
            pretty_data = json.dumps(data_str, indent=4)
            sync_write_file(inventory_path, pretty_data)

        except Exception as e:
            raise FailedOperation(
                u._('Saving inventory failed. : {error}')
                .format(error=str(e)))

    def get_hosts(self):
        return self._hosts.values()

    def get_hostnames(self):
        return list(self._hosts.keys())

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
            raise NotInInventory(u._('Group'), groupname)

        if groupname and hostname not in self._hosts:
            # if a groupname is specified, the host must already exist
            raise NotInInventory(u._('Host'), hostname)

        if not groupname and not self.remote_mode and len(self._hosts) >= 1:
            raise InvalidConfiguration(
                u._('Cannot have more than one host when in local deploy '
                    'mode.'))

        changed = False
        # create new host if it doesn't exist
        host = Host(hostname)
        if hostname not in self.get_hostnames():
            # a new host is being added to the inventory
            changed = True
            self._hosts[hostname] = host

        # a host is to be added to an existing group
        elif groupname:
            group = self._groups[groupname]
            if hostname not in group.get_hostnames():
                changed = True
                group.add_host(host)
        return changed

    def remove_all_hosts(self):
        """remove all hosts."""
        hostnamess = self.get_hostnames()
        for hostname in hostnamess:
            self.remove_host(hostname)

    def remove_host(self, hostname, groupname=None):
        """remove host

        if groupname is none, delete host
        if group name is not none, remove host from group
        """
        changed = False
        if groupname and groupname not in self._groups:
            raise NotInInventory(u._('Group'), groupname)

        if hostname not in self._hosts:
            return changed

        changed = True
        host = self._hosts[hostname]
        groups = self.get_groups(host)
        for group in groups:
            if not groupname or groupname == group.name:
                group.remove_host(host)

        host_vars = os.path.join(get_host_vars_dir(), hostname)
        if os.path.exists(host_vars):
            os.remove(host_vars)

        if not groupname:
            del self._hosts[hostname]
        return changed

    def setup_hosts(self, hosts_info):
        """setup multiple hosts

        hosts_info is a dict of format:
        {'hostname1': {
            'password': password
            'uname': user_name
            }
        }
        The uname entry is optional.
        """
        failed_hosts = {}
        for hostname, host_info in hosts_info.items():
            host = self.get_host(hostname)
            if not host:
                failed_hosts[hostname] = u._("Host doesn't exist.")
                continue
            if not host_info or 'password' not in host_info:
                failed_hosts[hostname] = u._('No password in yml file.')
                continue
            passwd = host_info['password']
            uname = None
            if 'uname' in host_info:
                uname = host_info['uname']
            try:
                self.setup_host(hostname, passwd, uname)
            except Exception as e:
                failed_hosts[hostname] = '%s' % e
        if failed_hosts:
            summary = '\n'
            for hostname, err in failed_hosts.items():
                summary = summary + '- %s: %s\n' % (hostname, err)
            raise HostError(
                u._('Not all hosts were set up. : {reasons}')
                .format(reasons=summary))
        else:
            LOG.info(u._LI('All hosts were successfully set up.'))

    def setup_host(self, hostname, password, uname=None):
        try:
            LOG.info(
                u._LI('Starting setup of host ({host}).')
                .format(host=hostname))
            check_ok, _ = self.ssh_check_host(hostname)
            if check_ok:
                LOG.info(u._LI('Host ({host}) is already setup.')
                         .format(host=hostname))
            else:
                # host needs setup
                ssh_setup_host(hostname, password, uname)
                check_ok, msg = self.ssh_check_host(hostname)
                if not check_ok:
                    raise Exception(u._('Post-setup ssh check failed. {err}')
                                    .format(err=msg))
                LOG.info(u._LI('Host ({host}) setup succeeded.')
                         .format(host=hostname))
        except Exception as e:
            raise HostError(
                u._('Host ({host}) setup failed : {error}')
                .format(host=hostname, error=str(e)))
        return True

    def ssh_check_hosts(self, hostnames):
        """ssh check for hosts

        return {hostname: {'success': True|False,
                           'msg': message}}
        """
        summary = {}
        for hostname in hostnames:
            is_ok, msg = self.ssh_check_host(hostname)
            summary[hostname] = {}
            summary[hostname]['success'] = is_ok
            summary[hostname]['msg'] = msg
        return summary

    def ssh_check_host(self, hostname):
        err_msg, output = self.run_ansible_command('-m ping', hostname)
        is_ok = True
        if err_msg:
            is_ok = False
            msg = (
                u._('Host ({host}) ssh check failed. : {error} {message}')
                .format(host=hostname, error=err_msg, message=output))
        else:
            msg = (u._LI('Host ({host}) ssh check succeeded.')
                   .format(host=hostname))
        return is_ok, msg

    def run_ansible_command(self, ansible_command, hostname):
        err_msg = None
        command_string = '/usr/bin/sudo -u %s %s -vvv' % \
            (get_admin_user(), get_ansible_command())
        gen_file_path = self.create_json_gen_file()
        cmd = '%s %s -i %s %s' % (command_string, hostname, gen_file_path,
                                  ansible_command)
        try:
            err_msg, output = run_cmd(cmd, False)
        except Exception as e:
            err_msg = str(e)
        finally:
            self.remove_json_gen_file(gen_file_path)
        return err_msg, output

    def add_group(self, groupname):

        # Group names cannot overlap with service names:
        if groupname in self._services or groupname in self._sub_services:
            raise InvalidArgument(
                u._('Invalid group name. A service name '
                    'cannot be used for a group name.'))

        if groupname not in self._groups:
            self._groups[groupname] = HostGroup(groupname)

        group = self._groups[groupname]

        group.set_remote(self.remote_mode)

        return group

    def remove_group(self, groupname):
        if groupname in PROTECTED_GROUPS:
            raise InvalidArgument(
                u._('Cannot remove {group} group. It is required by kolla.')
                .format(group=groupname))

        # remove group from services & subservices
        for service in self._services.values():
            service.remove_groupname(groupname)

        for subservice in self._sub_services.values():
            subservice.remove_groupname(groupname)

        group_vars = os.path.join(get_group_vars_dir(), groupname)
        if os.path.exists(group_vars) and groupname != '__GLOBAL__':
            os.remove(group_vars)

        if groupname in self._groups:
            del self._groups[groupname]

    def get_group(self, groupname):
        group = None
        if groupname in self._groups:
            group = self._groups[groupname]
        return group

    def get_groupnames(self):
        return list(self._groups.keys())

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

    def get_host_groups(self):
        """return { hostname : [groupnames] }"""

        host_groups = {}
        for host in self._hosts.values():
            host_groups[host.name] = []
            groups = self.get_groups(host)
            for group in groups:
                host_groups[host.name].append(group.name)
        return host_groups

    def get_group_services(self):
        """get groups and their services

        return { groupname: [servicenames] }
        """

        group_services = {}

        for group in self.get_groups():
            group_services[group.name] = []

        for svc in self.get_services():
            for groupname in svc.get_groupnames():
                group_services[groupname].append(svc.name)
        for sub_svc in self.get_sub_services():
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
            service = self._services[servicename]
            for sub_servicename in service.get_sub_servicenames():
                self.delete_sub_service(sub_servicename)
            del self._services[servicename]

    def get_services(self):
        return self._services.values()

    def get_service(self, servicename):
        service = None
        if servicename in self._services:
            service = self._services[servicename]
        return service

    def add_group_to_service(self, groupname, servicename):
        if groupname not in self._groups:
            raise NotInInventory(u._('Group'), groupname)
        if servicename in self._services:
            service = self.get_service(servicename)
            service.add_groupname(groupname)
        elif servicename in self._sub_services:
                sub_service = self.get_sub_service(servicename)
                sub_service.add_groupname(groupname)
        else:
            raise NotInInventory(u._('Service'), servicename)

    def remove_group_from_service(self, groupname, servicename):
        if groupname not in self._groups:
            raise NotInInventory(u._('Group'), groupname)
        if servicename in self._services:
            service = self.get_service(servicename)
            service.remove_groupname(groupname)
        elif servicename in self._sub_services:
                sub_service = self.get_sub_service(servicename)
                sub_service.remove_groupname(groupname)
        else:
            raise NotInInventory(u._('Service'), servicename)

    def create_sub_service(self, sub_servicename):
        if sub_servicename not in self._sub_services:
            sub_service = SubService(sub_servicename)
            self._sub_services[sub_servicename] = sub_service
        return self._sub_services[sub_servicename]

    def delete_sub_service(self, sub_servicename):
        if sub_servicename in self._sub_services:
            sub_service = self._sub_services[sub_servicename]
            parentname = sub_service.get_parent_servicename()
            parent = self._services[parentname]
            if sub_servicename in parent._sub_servicenames:
                parent._sub_servicenames.remove(sub_servicename)
            del self._sub_services[sub_servicename]

    def get_sub_services(self):
        return self._sub_services.values()

    def get_sub_service(self, sub_servicename):
        sub_service = None
        if sub_servicename in self._sub_services:
            sub_service = self._sub_services[sub_servicename]
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

    def set_deploy_mode(self, remote_flag):
        if not remote_flag and len(self._hosts) > 1:
            raise InvalidConfiguration(
                u._('Cannot set local deploy mode when multiple hosts exist.'))
        self.remote_mode = remote_flag

        for group in self.get_groups():
            group.set_remote(remote_flag)

    def get_ansible_json(self, inventory_filter=None):
        """generate json inventory for ansible

        The hosts and groups added to the json output for ansible will be
        filtered by the hostnames and groupnames in the deploy filters.
        This allows a more targeted deploy to a specific set of hosts or
        groups.

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

        # if no filter provided, use all groups, all hosts
        deploy_hostnames = self.get_hostnames()
        deploy_groupnames = self.get_groupnames()
        if inventory_filter:
            if 'deploy_hosts' in inventory_filter:
                deploy_hostnames = inventory_filter['deploy_hosts']
            if 'deploy_groups' in inventory_filter:
                deploy_groupnames = inventory_filter['deploy_groups']

        # add hostgroups
        for group in self.get_groups():
            jdict[group.name] = {}
            jdict[group.name]['hosts'] = []

            if group.name in deploy_groupnames:
                jdict[group.name]['hosts'] = \
                    self._filter_hosts(group.get_hostnames(), deploy_hostnames)
            jdict[group.name]['children'] = []
            jdict[group.name]['vars'] = group.get_vars()

        # add top-level services and what groups they are in
        for service in self.get_services():
            jdict[service.name] = {}
            jdict[service.name]['children'] = service.get_groupnames()

        # add sub-services and their groups
        for sub_svc in self.get_sub_services():
            jdict[sub_svc.name] = {}
            groupnames = sub_svc.get_groupnames()
            if groupnames:
                # sub-service is associated with a group(s)
                jdict[sub_svc.name]['children'] = groupnames
            else:
                # sub-service is associated with parent service
                jdict[sub_svc.name]['children'] = \
                    [sub_svc.get_parent_servicename()]

        # temporarily create group containing all hosts. this is needed for
        # ansible commands that are performed on hosts not yet in groups.
        group = self.add_group('__GLOBAL__')
        jdict[group.name] = {}
        jdict[group.name]['hosts'] = deploy_hostnames
        jdict[group.name]['vars'] = group.get_vars()
        self.remove_group(group.name)

        # process hosts vars
        jdict['_meta'] = {}
        jdict['_meta']['hostvars'] = {}
        for hostname in deploy_hostnames:
            host = self.get_host(hostname)
            if host:
                jdict['_meta']['hostvars'][hostname] = host.get_vars()
        return json.dumps(jdict)

    def _filter_hosts(self, initial_hostnames, deploy_hostnames):
        """filter out hosts not in deploy hosts

        Must preserve the ordering of hosts in the group.
        """
        filtered_hostnames = []
        for hostname in initial_hostnames:
            if hostname in deploy_hostnames:
                filtered_hostnames.append(hostname)
        return filtered_hostnames

    def create_json_gen_file(self, inventory_filter=None):
        """create json inventory file using filter ({})

        The inventory will be placed in a directory in /tmp,
        with the directory name of form kolla_uuid.py,
        where uuid is a unique deployment id.

        return path to filtered json generator file
        """
        json_out = self.get_ansible_json(inventory_filter)

        deploy_id = str(uuid.uuid4())
        dirname = 'kolla_%s' % deploy_id
        dirpath = os.path.join(tempfile.gettempdir(), dirname)
        os.mkdir(dirpath, 0o775)
        _, gid = get_admin_uids()
        os.chown(dirpath, -1, gid)  # nosec
        json_gen_path = os.path.join(dirpath, 'temp_inventory.py')

        with open(json_gen_path, 'w') as json_gen_file:
            json_gen_file.write('#!/usr/bin/env python\n')
            # the quotes here are significant. The json_out has double quotes
            # embedded in it so single quotes are needed to wrap it.
            json_gen_file.write("print('%s')" % json_out)

        # set executable by group
        os.chmod(json_gen_path, 0o555)  # nosec
        return json_gen_path

    def remove_json_gen_file(self, path):
        remove_temp_inventory(path)

    def validate_hostnames(self, hostnames):
        if not hostnames:
            raise MissingArgument(u._('Host name(s)'))
        invalid_hosts = []
        for hostname in hostnames:
            if hostname not in self._hosts:
                invalid_hosts.append(hostname)
        if invalid_hosts:
            raise NotInInventory(u._('Host'), invalid_hosts)

    def validate_groupnames(self, groupnames):
        if not groupnames:
            raise MissingArgument(u._('Group name(s)'))
        invalid_groups = []
        for groupname in groupnames:
            if groupname not in self._groups:
                invalid_groups.append(groupname)
        if invalid_groups:
            raise NotInInventory(u._('Group'), invalid_groups)

    def validate_servicenames(self, servicenames):
        if not servicenames:
            raise MissingArgument(u._('Service name(s)'))
        invalid_services = []
        for servicename in servicenames:
            if (servicename not in self._services and
                    servicename not in self._sub_services):
                invalid_services.append(servicename)
        if invalid_services:
            raise NotInInventory(u._('Service'), invalid_services)

    def _create_default_inventory(self):
        allin1 = AllInOne()
        for groupname in allin1.groups:
            self.add_group(groupname)
        for servicename, service in allin1.services.items():
            self._services[servicename] = service
        for sub_servicename, sub_service in allin1.sub_services.items():
            self._sub_services[sub_servicename] = sub_service
