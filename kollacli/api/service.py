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

from kollacli.common.inventory import Inventory
from kollacli.common.utils import check_arg
from kollacli.common.utils import safe_decode


class ServiceApi(object):

    class Service(object):
        """Service

        A service is one of the services available in openstack-kolla.

        For example, this would be how the murano services would be
        represented:

        - murano
            - parentname: None
            - childnames: [murano-api, murano-engine]
        - murano-api
            - parentname: murano
            - childnames: []
        - murano-engine
            - parentname: murano
            - childnames: []
        """
        def __init__(self, servicename, parentname=None,
                     childnames=[], groupnames=[]):
            self.name = servicename
            self.parentname = parentname
            self._childnames = childnames
            self._groupnames = groupnames

        def get_name(self):
            """Get name

            :return: service name
            :rtype: string
            """
            return self.name

        def get_parent(self):
            """Get name of parent service

            :return: parent service name
            :rtype: string
            """
            return self.parentname

        def get_children(self):
            """Get names of the child services associated with this service

            :return: child names
            :rtype: list of strings
            """
            return copy(self._childnames)

        def get_groups(self):
            """Get names of the groups associated with this service

            :return: group names
            :rtype: list of strings
            """
            return copy(self._groupnames)

    def service_get_all(self):
        """Get all services in the inventory

        :return: services
        :rtype: List of Service objects
        """
        return self._get_services(None, get_all=True)

    def service_get(self, servicenames):
        """Get selected services in the inventory

        :param servicenames: names of services to be read
        :type servicenames: list of strings
        :return: services
        :rtype: list of Service objects
        """
        check_arg(servicenames, u._('Service names'), list)
        servicenames = safe_decode(servicenames)
        return self._get_services(servicenames)

    def _get_services(self, servicenames, get_all=False):
        services = []
        inventory = Inventory.load()
        if servicenames:
            inventory.validate_servicenames(servicenames)

        inv_services = inventory.get_services()
        inv_subservices = inventory.get_sub_services()

        for inv_service in inv_services:
            if get_all or inv_service.name in servicenames:
                service = self.Service(inv_service.name,
                                       None,
                                       inv_service.get_sub_servicenames(),
                                       inv_service.get_groupnames())
                services.append(service)
        for inv_subservice in inv_subservices:
            if get_all or inv_subservice.name in servicenames:
                service = self.Service(inv_subservice.name,
                                       inv_subservice.get_parent_servicename(),
                                       [],
                                       inv_subservice.get_groupnames())
                services.append(service)
        return services
