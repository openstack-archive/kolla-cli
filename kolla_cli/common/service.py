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
        self._parentnames = []
        self._childnames = []
        self._groupnames = []
        self._supported = True
        self._vars = {}
        self.version = self.__class__.class_version

    def upgrade(self):
        pass

    def add_parentname(self, parentname):
        if parentname is not None and parentname not in self._parentnames:
            self._parentnames.append(parentname)

    def remove_parentname(self, parentname):
        if parentname in self._parentnames:
            self._parentnames.remove(parentname)

    def get_parentnames(self):
        return copy(self._parentnames)

    def add_groupname(self, groupname):
        if groupname is not None and groupname not in self._groupnames:
            self._groupnames.append(groupname)

    def remove_groupname(self, groupname):
        if groupname in self._groupnames:
            self._groupnames.remove(groupname)

    def set_groupnames(self, groupnames):
        self._groupnames = groupnames

    def get_groupnames(self):
        return copy(self._groupnames)

    def get_childnames(self):
        return copy(self._childnames)

    def add_childname(self, childname):
        if childname not in self._childnames:
            self._childnames.append(childname)

    def remove_childname(self, childname):
        if childname in self._childnames:
            self._childnames.remove(childname)

    def set_supported(self, supported):
        self._supported = supported

    def is_supported(self):
        return self._supported

    def get_vars(self):
        return self._vars.copy()
