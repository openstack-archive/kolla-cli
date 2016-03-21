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
import logging

from kollacli.api.exceptions import MissingArgument
from kollacli.common.inventory import Inventory
from kollacli.common.utils import safe_decode

LOG = logging.getLogger(__name__)


class HostApi(object):

    def host_add(self, hostnames):
        """add hosts to the inventory"""
        if not hostnames:
            raise MissingArgument('host names')
        hostnames = safe_decode(hostnames)

        inventory = Inventory.load()
        for hostname in hostnames:
            inventory.add_host(hostname)
        Inventory.save(inventory)

    def host_remove(self, hostnames):
        """remove hosts from the inventory"""
        inventory = Inventory.load()

        if not hostnames:
                raise MissingArgument('host name')

        hostnames = safe_decode(hostnames)
        for hostname in hostnames:
            inventory.remove_host(hostname)

        Inventory.save(inventory)

    def host_get_all(self):
        """get all hosts in the inventory"""
        # TODO(snoyes) - need to make a host object
        inventory = Inventory.load()
        hostnames = inventory.get_hostnames()
        return hostnames

    def host_get_groups(self, hostname=None):
        """get groups for hosts

        Return:
        - if hostname, {hostname: [groups]}
        - else, {hostname: [groups], hostname: [groups]...}
        """
        inventory = Inventory.load()
        host_groups = inventory.get_host_groups()
        if hostname:
            hostname = safe_decode(hostname)
            inventory.validate_hostnames([hostname])
            groupnames = host_groups[hostname]
            host_groups = {hostname: groupnames}
        return host_groups

    def host_check_ssh(self, hostnames):
        """ssh check for hosts

        return {hostname: {'success': True|False,
                           'msg': message}}
        """
        inventory = Inventory.load()
        hostnames = safe_decode(hostnames)
        inventory.validate_hostnames(hostnames)
        summary = inventory.ssh_check_hosts(hostnames)
        return summary

    def host_setup_hosts(self, hosts_info):
        """setup multiple hosts

        hosts_info is a dict of format:
        {'hostname1': {
            'password': password
            'uname': user_name
            }
        }
        The uname entry is optional.
        """
        inventory = Inventory.load()
        inventory.validate_hostnames(hosts_info.keys())
        inventory.setup_hosts(hosts_info)

    def host_setup(self, hostname, password):
        # TODO(snoyes) move to host object
        inventory = Inventory.load()
        hostname = safe_decode(hostname)
        inventory.validate_hostnames([hostname])
        inventory.setup_host(hostname, password)
