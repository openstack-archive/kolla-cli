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
from kottos.api.service import ServiceApi as KottosServiceApi


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
            self.service = KottosServiceApi.Service(servicename, parentname,
                                                    childnames, groupnames)
            self.parentname = self.service.parentname

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
            return self.service.get_children()

        def get_groups(self):
            """Get names of the groups associated with this service

            :return: group names
            :rtype: list of strings
            """
            return self.service.get_groups()

    def service_get_all(self):
        """Get all services in the inventory

        :return: services
        :rtype: List of Service objects
        """
        try:
            services = KottosServiceApi().service_get_all()
            new_services = []
            for service in services:
                new_service = self.Service(service.name,
                                           service.parentname,
                                           service.get_children(),
                                           service.get_groups())
                new_services.append(new_service)
            return new_services
        except Exception as e:
            reraise(e)

    def service_get(self, servicenames):
        """Get selected services in the inventory

        :param servicenames: names of services to be read
        :type servicenames: list of strings
        :return: services
        :rtype: list of Service objects
        """
        try:
            services = KottosServiceApi().service_get(servicenames)
            new_services = []
            for service in services:
                new_service = self.Service(service.name,
                                           service.parentname,
                                           service.get_children(),
                                           service.get_groups())
                new_services.append(new_service)
            return new_services
        except Exception as e:
            reraise(e)
