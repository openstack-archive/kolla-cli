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

from kollacli.common.inventory import Inventory

LOG = logging.getLogger(__name__)


class HostApi(object):

    def host_add(self, hostname):
        inventory = Inventory.load()
        inventory.add_host(hostname)
        Inventory.save(inventory)

    def host_remove(self, hostname):
        # TODO(bmace) - need to do a lot of validity
        # / null checking in these api calls
        inventory = Inventory.load()

        if hostname.lower() == 'all':
            inventory.remove_all_hosts()
        else:
            inventory.remove_host(hostname)

        Inventory.save(inventory)
