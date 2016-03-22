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
from kollacli.api.exceptions import MissingArgument
from kollacli.common.inventory import Inventory
from kollacli.common.utils import safe_decode


class GroupApi(object):

    def group_add(self, groupname):
        """add a group to the inventory

        :param groupname: name of the group to add to the inventory
        :param groupname: string

        """
        if not groupname:
            raise MissingArgument('group name')
        groupname = safe_decode(groupname)

        inventory = Inventory.load()
        inventory.add_group(groupname)
        Inventory.save(inventory)

    def group_remove(self, groupname):
        """remove a group from the inventory

        :param groupname: name of the group to remove from the inventory
        :param groupname: string

        """
        if not groupname:
            raise MissingArgument('group name')

        inventory = Inventory.load()
        groupname = safe_decode(groupname)
        inventory.remove_group(groupname)
        Inventory.save(inventory)
