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

from kolla_cli.common.inventory import Inventory
from kolla_cli.common.utils import check_arg
from kolla_cli.common.utils import safe_decode
import kolla_cli.i18n as u


MYPY = False
if MYPY:
    from typing import List  # noqa


class GroupApi(object):

    def group_add(self, groupnames):
        # type: (List[str]) -> None
        """Add groups to the inventory

        :param groupnames: names of the groups to add to the inventory
        :type groupnames: list of strings

        """
        check_arg(groupnames, u._('Group names'), list)
        groupnames = safe_decode(groupnames)

        inventory = Inventory.load()
        for groupname in groupnames:
            inventory.add_group(groupname)
        Inventory.save(inventory)

    def group_remove(self, groupnames):
        # type: (List[str]) -> None
        """Remove groups from the inventory

        :param groupnames: names of the groups to remove from the inventory
        :type groupnames: list of strings
        """
        check_arg(groupnames, u._('Group names'), list)
        groupnames = safe_decode(groupnames)

        inventory = Inventory.load()
        for groupname in groupnames:
            inventory.remove_group(groupname)
        Inventory.save(inventory)

    def group_get_all(self):
        # type: () -> List[Group]
        """Get all groups in the inventory

        :return: groups
        :rtype: list of Group objects
        """
        return self._get_groups([], get_all=True)

    def group_get(self, groupnames):
        # type: (List[str]) -> List[Group]
        """Get selected groups in the inventory

        :param groupnames: names of groups to be read
        :type groupnames: list of strings
        :return: groups
        :rtype: list of Group objects
        """
        check_arg(groupnames, u._('Group names'), list)
        groupnames = safe_decode(groupnames)
        return self._get_groups(groupnames)

    def _get_groups(self, groupnames, get_all=False):
        # type: (List[str], bool) -> List[Group]
        groups = []
        inventory = Inventory.load()
        if get_all:
            groupnames = inventory.get_groupnames()
        else:
            inventory.validate_groupnames(groupnames)

        group_services = inventory.get_group_services()
        for groupname in groupnames:
            inv_group = inventory.get_group(groupname)
            group = Group(groupname,
                          group_services[groupname],
                          inv_group.get_hostnames())
            groups.append(group)
        return groups


class Group(object):
    def __init__(self, groupname, servicenames, hostnames):
        # type: (str, List[str], List[str]) -> None
        self.name = groupname
        self._servicenames = servicenames
        self._hostnames = hostnames

    def get_name(self):
        # type: () -> str
        """Get name

        :return: group name
        :rtype: string
        """
        return self.name

    def get_services(self):
        # type: () -> List[str]
        """Get names of services associated with this group.

        :return: service names
        :rtype: list of strings
        """
        return copy(self._servicenames)

    def add_service(self, servicename):
        # type: (str) -> None
        """Add service to group

        :param servicename: name of the service to add to the group
        :type servicename: string
        """
        check_arg(servicename, u._('Service name'), str)
        servicename = safe_decode(servicename)
        inventory = Inventory.load()
        inventory.validate_servicenames([servicename], client_filter=True)

        group_services = inventory.get_group_services()
        self._servicenames = group_services[self.name]
        if servicename not in self._servicenames:
            # service not associated with group, add it
            inventory.add_group_to_service(self.name, servicename)
            self._servicenames.append(servicename)
            Inventory.save(inventory)

    def remove_service(self, servicename):
        # type: (str) -> None
        """Remove service from group

        :param servicename: name of the service to remove from the group
        :type servicename: string

        """
        check_arg(servicename, u._('Service name'), str)
        servicename = safe_decode(servicename)
        inventory = Inventory.load()
        inventory.validate_servicenames([servicename], client_filter=True)

        group_services = inventory.get_group_services()
        self._servicenames = group_services[self.name]
        if servicename in self._servicenames:
            # service is associated with group, remove it
            inventory.remove_group_from_service(self.name, servicename)
            self._servicenames.remove(servicename)
            Inventory.save(inventory)

    def get_hosts(self):
        # type: () -> List[str]
        """Get names of hosts associated with this group.

        :return: host names
        :rtype: list of strings
        """
        return copy(self._hostnames)

    def add_host(self, hostname):
        # type: (str) -> None
        """Add host to group

        :param hostname: name of the host to add to the group
        :type hostname: string

        """
        check_arg(hostname, u._('Host name'), str)
        hostname = safe_decode(hostname)
        inventory = Inventory.load()
        inventory.validate_hostnames([hostname])

        group = inventory.get_group(self.name)
        self._hostnames = group.get_hostnames()
        if hostname not in self._hostnames:
            # host not associated with group, add it
            inventory.add_host(hostname, self.name)
            self._hostnames.append(hostname)
            Inventory.save(inventory)

    def remove_host(self, hostname):
        # type: (str) -> None
        """Remove host from group

        :param hostname: name of the host to remove from the group
        :type hostname: string

        """
        check_arg(hostname, u._('Host name'), str)
        hostname = safe_decode(hostname)
        inventory = Inventory.load()
        inventory.validate_hostnames([hostname])

        group = inventory.get_group(self.name)
        self._hostnames = group.get_hostnames()
        if hostname in self._hostnames:
            # host is associated with group, remove it
            inventory.remove_host(hostname, self.name)
            self._hostnames.remove(hostname)
            Inventory.save(inventory)
