import logging

from kollaclient.i18n import _

from cliff.command import Command


class PropertySet(Command):
    "Property Set"

    log = logging.getLogger(__name__)

    def take_action(self, parsed_args):
        self.log.info(_("property set"))
        self.app.stdout.write(parsed_args)


class PropertyList(Command):
    "Property List"

    log = logging.getLogger(__name__)

    def take_action(self, parsed_args):
        self.log.info(_("property list"))
        self.app.stdout.write(parsed_args)
