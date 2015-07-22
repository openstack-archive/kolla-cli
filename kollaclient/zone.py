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
