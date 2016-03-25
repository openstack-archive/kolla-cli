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
import kollacli.i18n as u

from kollacli.api.exceptions import InvalidArgument
from kollacli.api.exceptions import MissingArgument
from kollacli.common.inventory import Inventory
from kollacli.common.utils import safe_decode


class HostApi(object):

    class Host(object):
        """Host"""
        def __init__(self, hostname, groupnames):
            self.name = hostname
            self._groupnames = groupnames

        def get_name(self):
            """Get name

            :return: host name
            :rtype: string
            """
            return self.name

        def get_groups(self):
            """Get names of the groups associated with this host

            :return: group names
            :rtype: list of strings
            """
            return copy(self._groupnames)

    def host_add(self, hostnames):
        """Add hosts to the inventory

        :param hostnames: list of strings
        """
        if not hostnames:
            raise MissingArgument(u._('Host names'))
        hostnames = safe_decode(hostnames)

        inventory = Inventory.load()
        any_changed = False
        for hostname in hostnames:
            changed = inventory.add_host(hostname)
            if changed:
                any_changed = True
        if any_changed:
            Inventory.save(inventory)

    def host_remove(self, hostnames):
        """Remove hosts from the inventory

        :param hostnames: list of strings
        """
        inventory = Inventory.load()

        if not hostnames:
                raise MissingArgument(u._('Host names'))

        hostnames = safe_decode(hostnames)
        any_changed = False
        for hostname in hostnames:
            changed = inventory.remove_host(hostname)
            if changed:
                any_changed = True
        if any_changed:
            Inventory.save(inventory)

    def host_get_all(self):
        """Get all hosts in the inventory

        :return: Hosts
        :rtype: Host
        """
        inventory = Inventory.load()
        hosts = []
        host_groups = inventory.get_host_groups()
        for hostname, groupnames in host_groups.items():
            hosts.append(self.Host(hostname, groupnames))
        return hosts

    def host_get(self, hostnames):
        """Get selected hosts in the inventory

        :param hostnames: list of strings
        :return: hosts
        :rtype: Host
        """
        if hostnames is None:
            raise MissingArgument(u._('Host names'))
        if not isinstance(hostnames, list):
            raise InvalidArgument(u._('Host names ({names}) is not a list')
                                  .format(names=hostnames))
        hostnames = safe_decode(hostnames)
        inventory = Inventory.load()
        inventory.validate_hostnames(hostnames)

        hosts = []
        host_groups = inventory.get_host_groups()
        for hostname in hostnames:
            hosts.append(self.Host(hostname, host_groups[hostname]))
        return hosts

    def host_ssh_check(self, hostnames):
        """Check hosts for ssh connectivity

        Check status is a dictionary of form:
        - {hostname: {
              'success':<True|False>,
              'msg':message_string},
           ...
          }

        :param hostnames: list of strings
        :return: check status
        :rtype: dictionary
        """
        inventory = Inventory.load()
        hostnames = safe_decode(hostnames)
        inventory.validate_hostnames(hostnames)
        summary = inventory.ssh_check_hosts(hostnames)
        return summary

    def host_setup(self, hosts_info):
        """Setup multiple hosts for ssh access

        hosts_info is a dictionary of form:
        {hostname': {
            'password': password
            'uname': user_name},
         ...
        }
        The uname entry is optional.

        :param hosts_info: dictionary
        """
        inventory = Inventory.load()
        inventory.validate_hostnames(hosts_info.keys())
        inventory.setup_hosts(hosts_info)
