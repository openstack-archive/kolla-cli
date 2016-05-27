# Copyright(c) 2016, Oracle and/or its affiliates.  All Rights Reserved.
#
#   Licensed under the Apache License, Version 2.0 (the "License"); you may
#   not use this file except in compliance with the License. You may obtain
#   a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#   WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#   License for the specific language governing permissions and limitations
#   under the License.
#
import os

from kollacli.common.service import Service
from kollacli.common.subservice import SubService

from kollacli.common.utils import get_kolla_home


class AllInOne(object):
    """AllInOne helper class

    This class parses the kolla all-in-one file and provides an
    easier to use way to represent that file.
    """
    def __init__(self):
        self.groups = []
        self.services = {}
        self.sub_services = {}

        self._load()

    def add_service(self, servicename):
        if servicename not in self.services:
            service = Service(servicename)
            self.services[servicename] = service
        return self.services[servicename]

    def add_sub_service(self, sub_servicename):
        if sub_servicename not in self.sub_services:
            sub_service = SubService(sub_servicename)
            self.sub_services[sub_servicename] = sub_service
        return self.sub_services[sub_servicename]

    def add_group(self, groupname):
        if groupname not in self.groups:
            self.groups.append(groupname)

    def _load(self):
        allineone_path = os.path.join(get_kolla_home(), 'ansible',
                                      'inventory_samples', 'all-in-one')
        with open(allineone_path, 'r') as ain1:
            ain1_inv = ain1.read()

        lines = ain1_inv.split('\n')
        for i in range(0, len(lines)):
            line = lines[i]
            if not line.startswith('['):
                continue
            line.strip()
            if ':children' not in line:
                groupname = line[1:len(line) - 1]
                self.add_group(groupname)
                continue

            sub_service = None
            sub_servicename = None
            servicename = line.split(':children')[0]
            servicename = servicename[1:]
            if '-' in servicename:
                sub_servicename = servicename
                servicename = sub_servicename.split('-', 1)[0]

            service = self.add_service(servicename)

            if sub_servicename:
                sub_service = self.add_sub_service(sub_servicename)
                sub_service.set_parent_servicename(servicename)
                service.add_sub_servicename(sub_servicename)

            # next line should be parent of service found above
            i += 1
            line = lines[i]
            parent = line.strip()
            if sub_service:
                if parent in self.groups:
                    sub_service.add_groupname(parent)

            else:
                service.add_groupname(parent)
