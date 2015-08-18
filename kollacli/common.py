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

from cliff.command import Command


class Deploy(Command):
    "Deploy"

    log = logging.getLogger(__name__)

    def take_action(self, parsed_args):
        kollaHome = get_kolla_home()
        kollaEtc = get_kolla_etc()
        self.log.info(kollaHome)
        commandString = 'ansible-playbook '
        inventoryString = '-i /home/bmace/devel/openstack-kollaclient/kollacli/ansible/json_generator.py '
        defaultsString = '-e @' + os.path.join(kollaEtc, 'defaults.yml')
        globalsString = ' -e @' + os.path.join(kollaEtc, 'globals.yml')
        passwordsString = ' -e @' + os.path.join(kollaEtc, 'passwords.yml')
        siteString = ' ' + os.path.join(kollaHome, 'ansible/site.yml')
        cmd = commandString + inventoryString + defaultsString + globalsString
        cmd = cmd + passwordsString + siteString
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
