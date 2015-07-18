import logging
import os

from kollaclient.i18n import _
from kollaclient.utils import get_kolla_etc
from kollaclient.utils import get_kolla_home

from cliff.command import Command


class Deploy(Command):
    "Deploy"

    log = logging.getLogger(__name__)

    def take_action(self, parsed_args):
        self.log.info(_("deploy"))
        self.app.stdout.write(''.join(parsed_args))


class Install(Command):
    "Install"

    log = logging.getLogger(__name__)

    def take_action(self, parsed_args):
        self.log.info(_("install"))
        self.app.stdout.write(''.join(parsed_args))


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
        kollaHome = get_kolla_home()
        kollaEtc = get_kolla_etc()
        self.log.info(_("start"))
        self.log.info(kollaHome)
        cmd = 'ansible-playbook -i'
        cmd = cmd + kollaHome + '/ansible/inventory/all-in-one'
        cmd = cmd + ' -e @' + kollaEtc + '/kolla/defaults.yml'
        cmd = cmd + ' -e @' + kollaEtc + '/kolla/globals.yml'
        cmd = cmd + ' -e @' + kollaEtc + '/kolla/passwords.yml'
        cmd = cmd + ' ' + kollaHome + '/ansible/site.yml'
        self.log.info(cmd)
        os.system(cmd)


class Stop(Command):
    "Stop"

    log = logging.getLogger(__name__)

    def take_action(self, parsed_args):
        self.log.info(_("stop"))


class Sync(Command):
    "Sync"

    log = logging.getLogger(__name__)

    def take_action(self, parsed_args):
        self.log.info(_("sync"))


class Upgrade(Command):
    "Upgrade"

    log = logging.getLogger(__name__)

    def take_action(self, parsed_args):
        self.log.info(_("upgrade"))
