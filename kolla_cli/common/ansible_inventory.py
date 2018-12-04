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

from kolla_cli.common.service import Service
from kolla_cli.common.utils import get_kolla_ansible_home


class AnsibleInventory(object):
    """AnsibleInventory helper class

    This class parses an ansible inventory file and provides an
    easier to use way to represent that file.
    """
    def __init__(self, inventory_path=None):
        self.groups = []
        self.services = {}
        self.group_vars = {}
        self.host_vars = {}

        self._load(inventory_path)

    def add_service(self, servicename):
        if servicename not in self.services:
            service = Service(servicename)
            self.services[servicename] = service
        return self.services[servicename]

    def add_group(self, groupname):
        if groupname not in self.groups:
            self.groups.append(groupname)

    def _load(self, inventory_path):
        """load an ansible inventory file

        Note: This assumes that there will be a blank line between each
        section:

        # Mistral
        [mistral-api:children]
        mistral

        [mistral-executor:children]
        mistral
        """
        if not inventory_path:
            inventory_path = os.path.join(
                get_kolla_ansible_home(), 'ansible', 'inventory',
                'all-in-one')
        with open(inventory_path, 'r') as ain1:
            ain1_inv = ain1.read()

        lines = [x for x in ain1_inv.split('\n') if not x.startswith('#')]
        for i in range(0, len(lines)):
            line = lines[i]
            if not line.startswith('['):
                continue
            line.strip()
            if ':vars' in line:
                # this is defining a set of group vars in the next set
                # of lines.
                groupname = line.split(':')[0]
                i = self._process_group_vars(groupname, lines, i)
                continue
            if ':children' not in line:
                groupname = line[1:len(line) - 1]
                self.add_group(groupname)
                continue

            servicename = line.split(':children')[0]
            servicename = servicename[1:]
            service = self.add_service(servicename)

            # next lines will be parents or groups for service found above
            has_parents_or_groups = False
            while True:
                i += 1
                line = lines[i]
                parent_or_group = line.strip()
                if parent_or_group.startswith('#'):
                    # comment line, skip
                    continue
                if not parent_or_group:
                    # blank line, done processing parents
                    # if a service has no parent or group associations
                    # we infer that it is not supported and is filtered
                    # from being shown to the client
                    service.set_supported(has_parents_or_groups)
                    break
                if parent_or_group in self.groups:
                    service.add_groupname(parent_or_group)
                    has_parents_or_groups = True
                else:
                    service.add_parentname(parent_or_group)
                    has_parents_or_groups = True

        for _, service in self.services.items():
            for parentname in service.get_parentnames():
                parent = self.services[parentname]
                if parent:
                    parent.add_childname(service.name)

    def _process_group_vars(self, groupname, lines, i):
        # currently group vars are ignored
        while True:
            i += 1
            line = lines[i].strip()
            if not line:
                break
