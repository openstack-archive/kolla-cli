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
import logging

from kollaclient.i18n import _
from kollaclient.util import load_etc_yaml
from kollaclient.util import save_etc_yaml

from cliff.command import Command


class ZoneAdd(Command):
    "Zone Add"

    log = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super(ZoneAdd, self).get_parser(prog_name)
        parser.add_argument('zonename')
        return parser

    def take_action(self, parsed_args):
        zonename = parsed_args.zonename
        contents = load_etc_yaml('zone.yml')
        for zone in contents:
            if zone == zonename:
                # TODO(bmace) fix message
                self.log.info(_("zone already exists"))
                return
        zoneEntry = {zonename: {'': ''}}
        contents.update(zoneEntry)
        save_etc_yaml('zone.yml', contents)


class ZoneRemove(Command):
    "Zone Remove"

    log = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super(ZoneRemove, self).get_parser(prog_name)
        parser.add_argument('zonename')
        return parser

    def take_action(self, parsed_args):
        zonename = parsed_args.zonename
        contents = load_etc_yaml('zone.yml')
        foundZone = False
        for zone in contents.items():
            if zone == zonename:
                foundZone = True
        if foundZone:
            del contents[zonename]
        else:
            # TODO(bmace) fix message
            self.log.info("no zone iby name (" + zonename + ") found")
        save_etc_yaml('zone.yml', contents)


class ZoneList(Command):
    "Zone List"

    log = logging.getLogger(__name__)

    def take_action(self, parsed_args):
        self.log.info(_("zone list"))
        contents = load_etc_yaml('zone.yml')
        for zone in contents:
            self.log.info(zone)
