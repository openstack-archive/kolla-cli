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
import kollacli.i18n as u

from kollacli.api.exceptions import MissingArgument
from kollacli.common.inventory import Inventory
from kollacli.common.utils import safe_decode


class GroupApi(object):

    class Group(object):
        def __init__(self, groupname, servicenames, hostnames):
            self.name = groupname
            self.servicenames = servicenames
            self.hostnames = hostnames

        def get_name(self):
            """Get name

            :return: group name
            :rtype: string
            """
            return self.name

        def get_servicenames(self):
            """Get service names associated with this group.

            :return: service names
            :rtype: list of strings
            """
            return self.servicenames

        def get_hostnames(self):
            """Get host names associated with this group.

            :return: host names
            :rtype: list of strings
            """
            return self.hostnames

    def group_add(self, groupname):
        """Add a group to the inventory

        :param groupname: name of the group to add to the inventory
        :type groupname: string

        """
        if not groupname:
            raise MissingArgument('Group name')
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
            raise MissingArgument('Group name')

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
            raise(MissingArgument(u._('Group names')))
        groupnames = safe_decode(groupnames)
        return self._get_groups(groupnames)

    def _get_groups(self, groupnames, get_all=False):
        groups = []
        inventory = Inventory.load()
        group_services = inventory.get_group_services()
        inv_groups = inventory.get_groups()
        for inv_group in inv_groups:
            if get_all or inv_group.name in groupnames:
                group = self.Group(inv_group.name,
                                   group_services[inv_group.name],
                                   inv_group.get_hostnames())
                groups.append(group)
        return groups
