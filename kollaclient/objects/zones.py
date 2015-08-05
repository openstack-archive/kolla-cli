# Copyright(c) 2015, Oracle and/or its affiliates.  All Rights Reserved.
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

import kollaclient.utils as utils


class Zones(object):
    _zones = []

    def __init__(self):
        yml = utils.load_etc_yaml('zones.yml')
        self._zones = yml.keys()

    def save(self):
        info = {}
        for zone in self._zones:
            info[zone] = ''
        utils.save_etc_yaml('zones.yml', info)

    def add_zone(self, zone_name):
        if zone_name not in self._zones:
            self._zones.append(zone_name)

    def remove_zone(self, zone_name):
        if zone_name in self._zones:
            self._zones.remove(zone_name)

    def get_all(self):
        return self._zones
