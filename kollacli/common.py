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
import os
import subprocess

from kollacli.i18n import _
from kollacli.utils import get_kolla_etc
from kollacli.utils import get_kolla_home
from kollacli.utils import get_kollacli_home

from cliff.command import Command


class Deploy(Command):
    "Deploy"

    log = logging.getLogger(__name__)

    def take_action(self, parsed_args):
        kollacli_home = get_kollacli_home()
        kolla_home = get_kolla_home()
        kolla_etc = get_kolla_etc()
        command_string = 'ansible-playbook '
        inventory_string = '-i ' + os.path.join(kollacli_home,
                                               'kollacli/ansible',
                                               'json_generator.py ')
        default_string = '-e @' + os.path.join(kolla_etc, 'defaults.yml')
        globals_string= ' -e @' + os.path.join(kolla_etc, 'globals.yml')
        passwords_string = ' -e @' + os.path.join(kolla_etc, 'passwords.yml')
        site_string = ' ' + os.path.join(kolla_home, 'ansible/site.yml')
        cmd = command_string + inventory_string + default_string + globals_string
        cmd = cmd + passwords_string + site_string
        self.log.debug('cmd:' + cmd)
        output, error = subprocess.Popen(cmd.split(' '),
                                         stdout=subprocess.PIPE,
                                         stderr=subprocess.PIPE).communicate()
        self.log.info(output)
        self.log.info(error)


class Install(Command):
    "Install"

    log = logging.getLogger(__name__)

    def take_action(self, parsed_args):
        self.log.info(_("install"))


class List(Command):
    "List"

    log = logging.getLogger(__name__)

    def take_action(self, parsed_args):
        self.log.info(_("list"))


class Start(Command):
    "Start"

    log = logging.getLogger(__name__)

    def take_action(self, parsed_args):
        self.log.info(_("start"))


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


class Dump(Command):
    "Dump"

    log = logging.getLogger(__name__)

    def take_action(self, parsed_args):
        self.log.info(_("dump"))
