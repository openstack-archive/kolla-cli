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
from kollacli.common.utils import reraise
from kottos.api.group import GroupApi as KottosGroupApi


class GroupApi(object):

    class Group(object):
        def __init__(self, groupname, servicenames, hostnames):
            self.group = KottosGroupApi.Group(groupname, servicenames,
                                              hostnames)
            self.name = groupname

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
            try:
                return self.group.get_services()
            except Exception as e:
                reraise(e)

        def add_service(self, servicename):
            """Add service to group

            :param servicename: name of the service to add to the group
            :type servicename: string

            """
            try:
                self.group.add_service(servicename)
            except Exception as e:
                reraise(e)

        def remove_service(self, servicename):
            """Remove service from group

            :param servicename: name of the service to remove from the group
            :type servicename: string

            """
            try:
                self.group.remove_service(servicename)
            except Exception as e:
                reraise(e)

        def get_hosts(self):
            """Get names of hosts associated with this group.

            :return: host names
            :rtype: list of strings
            """
            try:
                return self.group.get_hosts()
            except Exception as e:
                reraise(e)

        def add_host(self, hostname):
            """Add host to group

            :param hostname: name of the host to add to the group
            :type hostname: string

            """
            try:
                self.group.add_host(hostname)
            except Exception as e:
                reraise(e)

        def remove_host(self, hostname):
            """Remove host from group

            :param hostname: name of the host to remove from the group
            :type hostname: string

            """
            try:
                self.group.remove_host(hostname)
            except Exception as e:
                reraise(e)

    def group_add(self, groupnames):
        """Add groups to the inventory

        :param groupnames: names of the groups to add to the inventory
        :type groupnames: list of strings

        """
        try:
            KottosGroupApi().group_add(groupnames)
        except Exception as e:
            reraise(e)

    def group_remove(self, groupnames):
        """Remove groups from the inventory

        :param groupnames: names of the groups to remove from the inventory
        :type groupnames: list of strings

        """
        try:
            KottosGroupApi().group_remove(groupnames)
        except Exception as e:
            reraise(e)

    def group_get_all(self):
        """Get all groups in the inventory

        :return: groups
        :rtype: list of Group objects
        """
        try:
            groups = KottosGroupApi().group_get_all()
            new_groups = []
            for group in groups:
                new_group = self.Group(group.name, group.get_services(),
                                       group.get_hosts())
                new_groups.append(new_group)
            return new_groups
        except Exception as e:
            reraise(e)

    def group_get(self, groupnames):
        """Get selected groups in the inventory

        :param groupnames: names of groups to be read
        :type groupnames: list of strings
        :return: groups
        :rtype: list of Group objects
        """
        try:
            groups = KottosGroupApi().group_get(groupnames)
            new_groups = []
            for group in groups:
                new_group = self.Group(group.name, group.get_services(),
                                       group.get_hosts())
                new_groups.append(new_group)
            return new_groups
        except Exception as e:
            reraise(e)
