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

from kollacli.api.exceptions import MissingArgument
from kollacli.common.inventory import Inventory
from kollacli.common.utils import safe_decode


class GroupApi(object):

    class Group(object):
        def __init__(self, groupname, servicenames, hostnames):
            self.name = groupname
            self._servicenames = servicenames
            self._hostnames = hostnames

        def get_name(self):
            """Get name

            :return: group name
            :rtype: string
            """
            return self.name

        def get_services(self):
            """Get names of services associated with this group.

            :return: service names
            :rtype: list of strings
            """
            return copy(self._servicenames)

        def add_service(self, servicename):
            """Add service to group

            :param servicename: name of the service to add to the group
            :type servicename: string

            """
            servicename = safe_decode(servicename)
            inventory = Inventory.load()
            inventory.validate_servicenames([servicename])

            group_services = inventory.get_group_services()
            self._servicenames = group_services[self.name]
            if servicename not in self._servicenames:
                # service not associated with group, add it
                inventory.add_group_to_service(self.name, servicename)
                Inventory.save(inventory)

        def remove_service(self, servicename):
            """Remove service from group

            :param servicename: name of the service to remove from the group
            :type servicename: string

            """
            servicename = safe_decode(servicename)
            inventory = Inventory.load()
            inventory.validate_servicenames([servicename])

            group_services = inventory.get_group_services()
            self._servicenames = group_services[self.name]
            if servicename in self._servicenames:
                # service is associated with group, remove it
                inventory.remove_group_from_service(self.name, servicename)
                Inventory.save(inventory)

        def get_hosts(self):
            """Get names of hosts associated with this group.

            :return: host names
            :rtype: list of strings
            """
            return copy(self._hostnames)

        def add_host(self, hostname):
            """Add host to group

            :param hostname: name of the host to add to the group
            :type hostname: string

            """
            hostname = safe_decode(hostname)
            inventory = Inventory.load()
            inventory.validate_hostnames([hostname])

            group = inventory.get_group(self.name)
            self._hostnames = group.get_hostnames()
            if hostname not in self._hostnames:
                # host not associated with group, add it
                inventory.add_host(hostname, self.name)
                Inventory.save(inventory)

        def remove_host(self, hostname):
            """Remove host from group

            :param hostname: name of the host to remove from the group
            :type hostname: string

            """
            hostname = safe_decode(hostname)
            inventory = Inventory.load()
            inventory.validate_hostnames([hostname])

            group = inventory.get_group(self.name)
            self._hostnames = group.get_hostnames()
            if hostname in self._hostnames:
                # host is associated with group, remove it
                inventory.remove_host(hostname, self.name)
                Inventory.save(inventory)

    def group_add(self, groupname):
        """Add a group to the inventory

        :param groupname: name of the group to add to the inventory
        :type groupname: string

        """
        if not groupname:
            raise MissingArgument(u._('Group name'))
        groupname = safe_decode(groupname)

        inventory = Inventory.load()
        inventory.add_group(groupname)
        Inventory.save(inventory)

    def group_remove(self, groupname):
        """Remove a group from the inventory

        :param groupname: name of the group to remove from the inventory
        :type groupname: string

        """
        if not groupname:
            raise MissingArgument(u._('Group name'))

        inventory = Inventory.load()
        groupname = safe_decode(groupname)
        inventory.remove_group(groupname)
        Inventory.save(inventory)

    def group_get_all(self):
        """Get all groups in the inventory

        :return: groups
        :rtype: list of Group objects
        """
        return self._get_groups(None, get_all=True)

    def group_get(self, groupnames):
        """Get selected groups in the inventory

        :param groupnames: names of groups to be read
        :type groupnames: list of strings
        :return: groups
        :rtype: list of Group objects
        """
        if groupnames is None:
            raise MissingArgument(u._('Group names'))
        groupnames = safe_decode(groupnames)
        return self._get_groups(groupnames)

    def _get_groups(self, groupnames, get_all=False):
        groups = []
        inventory = Inventory.load()
        if groupnames:
            inventory.validate_groupnames(groupnames)

        group_services = inventory.get_group_services()
        inv_groups = inventory.get_groups()
        for inv_group in inv_groups:
            if get_all or inv_group.name in groupnames:
                group = self.Group(inv_group.name,
                                   group_services[inv_group.name],
                                   inv_group.get_hostnames())
                groups.append(group)
        return groups
