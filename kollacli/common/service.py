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
from copy import copy


class Service(object):
    class_version = 1

    def __init__(self, name):
        self.name = name
        self._sub_servicenames = []
        self._groupnames = []
        self._vars = {}
        self.version = self.__class__.class_version

    def upgrade(self):
        pass

    def add_groupname(self, groupname):
        if groupname is not None and groupname not in self._groupnames:
            self._groupnames.append(groupname)

    def remove_groupname(self, groupname):
        if groupname in self._groupnames:
            self._groupnames.remove(groupname)

    def get_groupnames(self):
        return copy(self._groupnames)

    def get_sub_servicenames(self):
        return copy(self._sub_servicenames)

    def add_sub_servicename(self, sub_servicename):
        if sub_servicename not in self._sub_servicenames:
            self._sub_servicenames.append(sub_servicename)

    def get_vars(self):
        return self._vars.copy()
