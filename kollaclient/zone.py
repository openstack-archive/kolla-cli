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

from kollaclient.utils import Zones

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
        zones = Zones()
        zones.add_zone(zonename)
        zones.save()


class ZoneRemove(Command):
    "Zone Remove"

    log = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super(ZoneRemove, self).get_parser(prog_name)
        parser.add_argument('zonename')
        return parser

    def take_action(self, parsed_args):
        zonename = parsed_args.zonename
        zones = Zones()
        zones.remove_zone(zonename)
        zones.save()


class ZoneList(Command):
    "Zone List"

    log = logging.getLogger(__name__)

    def take_action(self, parsed_args):
        output = ''
        for zone in Zones().get_all():
            if output:
                output = output + ', '
            output = output + zone
        self.log.info(output)
