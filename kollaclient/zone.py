import logging

from kollaclient.i18n import _

from cliff.command import Command


class ZoneAdd(Command):
    "Zone Add"

    log = logging.getLogger(__name__)

    def take_action(self, parsed_args):
        self.log.info(_("zone add"))
        self.app.stdout.write(parsed_args)


class ZoneRemove(Command):
    "Zone Remove"

    log = logging.getLogger(__name__)

    def take_action(self, parsed_args):
        self.log.info(_("zone remove"))
        self.app.stdout.write(parsed_args)


class ZoneList(Command):
    "Zone List"

    log = logging.getLogger(__name__)

    def take_action(self, parsed_args):
        self.log.info(_("zone list"))
        self.app.stdout.write(parsed_args)
