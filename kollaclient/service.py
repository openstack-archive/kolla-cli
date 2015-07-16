import logging

from kollaclient.i18n import _

from cliff.command import Command


class ServiceActivate(Command):
    "Service Activate"

    log = logging.getLogger(__name__)

    def take_action(self, parsed_args):
        self.log.info(_("service activate"))
        self.app.stdout.write(parsed_args)


class ServiceDeactivate(Command):
    "Service Deactivate"

    log = logging.getLogger(__name__)

    def take_action(self, parsed_args):
        self.log.info(_("service deactivate"))
        self.app.stdout.write(parsed_args)


class ServiceAutodeploy(Command):
    "Service Autodeploy"

    log = logging.getLogger(__name__)

    def take_action(self, parsed_args):
        self.log.info(_("service autodeploy"))
        self.app.stdout.write(parsed_args)


class ServiceList(Command):
    "Service List"

    log = logging.getLogger(__name__)

    def take_action(self, parsed_args):
        self.log.info(_("service list"))
        self.app.stdout.write(parsed_args)
