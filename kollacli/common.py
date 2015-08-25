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
import traceback

from kollacli.ansible.inventory import Inventory
from kollacli.exceptions import CommandError
from kollacli.i18n import _
from kollacli.utils import get_kolla_etc
from kollacli.utils import get_kolla_home
from kollacli.utils import get_kollacli_home

from cliff.command import Command


class Deploy(Command):
    """Deploy"""

    log = logging.getLogger(__name__)

    def take_action(self, parsed_args):
        try:
            debug = False
            flag = ''
            if self.log.getEffectiveLevel() <= logging.DEBUG:
                flag = '-vvv'
                debug = True

            kollacli_home = get_kollacli_home()
            kolla_home = get_kolla_home()
            kolla_etc = get_kolla_etc()
            command_string = 'ansible-playbook %s ' % flag
            inventory_string = '-i ' + os.path.join(kollacli_home,
                                                    'tools',
                                                    'json_generator.py ')
            globals_string = ' -e @' + os.path.join(kolla_etc,
                                                    'globals.yml')
            passwords_string = ' -e @' + os.path.join(kolla_etc,
                                                      'passwords.yml')
            site_string = ' ' + os.path.join(kolla_home, 'ansible/site.yml')
            cmd = (command_string + inventory_string + globals_string)
            cmd = cmd + passwords_string + site_string

            if debug:
                self.log.debug('cmd:' + cmd)

                dbg_gen = os.path.join(kollacli_home, 'tools',
                                       'json_generator.py ')
                (inv, _) = \
                    subprocess.Popen(dbg_gen.split(' '),
                                     stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE).communicate()
                self.log.debug(inv)

            err_flag = self.run_and_peek(cmd)
            if err_flag:
                raise Exception('deploy failed')

            self.log.info('deploy succeeded')
        except CommandError as e:
            raise e
        except Exception as e:
            raise Exception(traceback.format_exc())

    def run_and_peek(self, cmd):
        import pexpect
        err_flag = False
        child = pexpect.spawn(cmd)
        child.maxsize = 1
        child.timeout = 86400
        for line in child:
            self.log.info(line.rstrip())
        child.close()
        if child.exitstatus != 0:
            err_flag = True
        return err_flag


class Install(Command):
    """Install"""

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


class Setdeploy(Command):
    """Set deploy mode

    Set deploy mode to either local or remote. Local indicates
    that the openstack deployment will be to the local host.
    Remote means that the deployment is on remote hosts.
    """
    def get_parser(self, prog_name):
        parser = super(Setdeploy, self).get_parser(prog_name)
        parser.add_argument('mode', metavar='<mode>',
                            help='mode=<local, remote>')
        return parser

    def take_action(self, parsed_args):
        try:
            mode = parsed_args.mode.strip()
            remote_flag = False
            if mode == 'remote':
                remote_flag = True
            elif mode != 'local':
                raise CommandError('Invalid deploy mode. Mode must be ' +
                                   'either "local" or "remote"')
            inventory = Inventory.load()
            inventory.set_deploy_mode(remote_flag)
            Inventory.save(inventory)
        except CommandError as e:
            raise e
        except Exception as e:
            raise Exception(traceback.format_exc())
