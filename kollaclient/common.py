import logging

from kollaclient.i18n import _

from cliff.command import Command


class Deploy(Command):
    "Deploy"

    log = logging.getLogger(__name__)

    def take_action(self, parsed_args):
        self.log.info(_("deploy"))
        self.app.stdout.write(parsed_args)


class List(Command):
    "List"

    log = logging.getLogger(__name__)

    def take_action(self, parsed_args):
        self.log.info(_("list"))
        self.app.stdout.write(parsed_args)


class Start(Command):
    "Start"

    log = logging.getLogger(__name__)

    def take_action(self, parsed_args):
        self.log.info(_("start"))
        self.app.stdout.write(parsed_args)


class Stop(Command):
    "Stop"

    log = logging.getLogger(__name__)

    def take_action(self, parsed_args):
        self.log.info(_("stop"))
        self.app.stdout.write(parsed_args)


class Sync(Command):
    "Sync"

    log = logging.getLogger(__name__)

    def take_action(self, parsed_args):
        self.log.info(_("sync"))
        self.app.stdout.write(parsed_args)


class Upgrade(Command):
    "Upgrade"

    log = logging.getLogger(__name__)

    def take_action(self, parsed_args):
        self.log.info(_("upgrade"))
        self.app.stdout.write(parsed_args)
