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


class ServiceApi(object):

    def service_get_all(self):
        # type: () -> List[Service]
        """Get all services in the inventory

        :return: services
        :rtype: List of Service objects
        """
        return self._get_services([], get_all=True)

    def service_get(self, servicenames):
        # type: (List[str]) -> List[Service]
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
        # type: (List[str], bool) -> List[Service]
        services = []
        inventory = Inventory.load()

        if get_all:
            inv_services = inventory.get_services(client_filter=True)
            for inv_service in inv_services:
                service = Service(inv_service.name,
                                  inv_service.get_parentnames(),
                                  inv_service.get_childnames(),
                                  inv_service.get_groupnames())
                services.append(service)
        else:
            inventory.validate_servicenames(servicenames, client_filter=True)

            for servicename in servicenames:
                inv_service = inventory.get_service(servicename,
                                                    client_filter=True)
                if inv_service:
                    service = Service(inv_service.name,
                                      inv_service.get_parentnames(),
                                      inv_service.get_childnames(),
                                      inv_service.get_groupnames())
                services.append(service)
        return services


class Service(object):
    """Service

    A service is one of the services available in openstack-kolla-ansible.

    For example, this would be how the murano services would be
    represented:

    - murano
        - parentnames: []
        - childnames: [murano-api, murano-engine]
    - murano-api
        - parentnames: [murano]
        - childnames: []
    - murano-engine
        - parentnames: [murano]
        - childnames: []
    """

    def __init__(self, servicename, parentnames=[],
                 childnames=[], groupnames=[]):
        # type: (str, List[str], List[str], List[str]) -> None
        self.name = servicename
        self._parentnames = parentnames
        self._childnames = childnames
        self._groupnames = groupnames

    def get_name(self):
        # type: () -> str
        """Get name

        :return: service name
        :rtype: string
        """
        return self.name

    def get_parents(self):
        # type: () -> List[str]
        """Get name of parent services

        :return: parent service names
        :rtype: string
        """
        return copy(self._parentnames)

    def get_children(self):
        # type: () -> List[str]
        """Get names of the child services

        :return: child names
        :rtype: list of strings
        """
        return copy(self._childnames)

    def get_groups(self):
        # type: () -> List[str]
        """Get names of the groups

        :return: group names
        :rtype: list of strings

        Note: If the groups associated with this service change after this
        service is fetched, the service must be re-fetched to reflect those
        changes.
        """
        return copy(self._groupnames)
