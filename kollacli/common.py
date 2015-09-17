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
import tarfile
import tempfile
import traceback

from kollacli.ansible.inventory import Inventory
from kollacli.exceptions import CommandError
from kollacli.i18n import _
from kollacli.utils import convert_to_unicode
from kollacli.utils import get_kolla_etc
from kollacli.utils import get_kolla_home
from kollacli.utils import get_kollacli_etc
from kollacli.utils import get_kollacli_home
from kollacli.utils import run_cmd

from cliff.command import Command


class Deploy(Command):
    """Deploy"""

    log = logging.getLogger(__name__)

    def take_action(self, parsed_args):
        try:
            flag = ''
            # verbose levels: 1=not verbose, 2=more verbose
            if self.app.options.verbose_level > 1:
                flag = '-vvv'

            kollacli_home = get_kollacli_home()
            kolla_home = get_kolla_home()
            kolla_etc = get_kolla_etc()
            command_string = 'sudo -u kolla ansible-playbook %s ' % flag
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

            if self.app.options.verbose_level > 1:
                # log the ansible command
                self.log.debug('cmd:' + cmd)

                if self.app.options.verbose_level > 2:
                    # log the inventory
                    dbg_gen = os.path.join(kollacli_home, 'tools',
                                           'json_generator.py ')
                    (inv, _) = \
                        subprocess.Popen(dbg_gen.split(' '),
                                         stdout=subprocess.PIPE,
                                         stderr=subprocess.PIPE).communicate()
                    self.log.debug(inv)

            err_flag, _ = run_cmd(cmd, True)
            if err_flag:
                raise Exception('deploy failed')

            self.log.info('deploy succeeded')
        except CommandError as e:
            raise e
        except Exception as e:
            raise Exception(traceback.format_exc())


class List(Command):
    "List"

    log = logging.getLogger(__name__)

    def take_action(self, parsed_args):
        self.log.info(_("list"))


class Dump(Command):
    """Dumps configuration data for debugging

    Dumps most files in /etc/kolla and /usr/share/kolla into a
    tar file so be given to support / development to help with
    debugging problems.
    """
    log = logging.getLogger(__name__)

    def take_action(self, parsed_args):
        try:
            kolla_home = get_kolla_home()
            kolla_ansible = os.path.join(kolla_home, 'ansible')
            kolla_docs = os.path.join(kolla_home, 'docs')
            kollacli_home = get_kollacli_home()
            kolla_templates = os.path.join(kolla_home, 'templates')
            kolla_etc = get_kolla_etc()
            kolla_config = os.path.join(kolla_etc, 'config')
            kolla_globals = os.path.join(kolla_etc, 'globals.yml')
            kollacli_etc = get_kollacli_etc()
            ketc = 'kolla/etc/'
            kshare = 'kolla/share/'
            dump_postfix = '_kollacli_dump.tgz'
            dump_file = tempfile.mktemp() + dump_postfix
            with tarfile.open(dump_file, "w:gz") as tar:
                # Can't blanket add kolla_home because the .ssh dir is
                # accessible by the kolla user only (not kolla group)
                tar.add(kolla_ansible,
                        arcname=ketc + os.path.basename(kolla_ansible))
                tar.add(kolla_docs,
                        arcname=ketc + os.path.basename(kolla_docs))
                tar.add(kollacli_home,
                        arcname=ketc + os.path.basename(kollacli_home))
                if os.path.isdir(kolla_templates):
                    tar.add(kolla_templates,
                            arcname=ketc + os.path.basename(kolla_templates))

                # Can't blanket add kolla_etc because the passwords.yml
                # file is accessible by the kolla user only (not kolla group)
                tar.add(kolla_config,
                        arcname=kshare + os.path.basename(kolla_config))
                tar.add(kolla_globals,
                        arcname=kshare + os.path.basename(kolla_globals))
                tar.add(kollacli_etc,
                        arcname=kshare + os.path.basename(kollacli_etc))
            self.log.info('dump successful to %s' % dump_file)
        except Exception:
            raise Exception(traceback.format_exc())


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
        except Exception:
            raise Exception(traceback.format_exc())

class Stop(Command):
    """Stop

    Stops and removes all containers on either the specified host
    or if no host is specified, on all hosts.
    """
    log = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super(Stop, self).get_parser(prog_name)
        parser.add_argument('hostname', nargs='?', metavar='[hostname]',
                            help='hostname')
        return parser

    def take_action(self, parsed_args):
        try:
            hostname = 'all' 
            if parsed_args.hostname:
                hostname = parsed_args.hostname.strip()
                hostname = convert_to_unicode(hostname)

            inventory = Inventory.load()

            if hostname != None and hostname != 'all':
                host = inventory.get_host(hostname)
                if not host:
                    raise CommandError(
                        'ERROR: Host (%s) not found. ' % hostname +
                        'Please add it with "host add"')

            flag = ''
            # verbose levels: 1=not verbose, 2=more verbose
            if self.app.options.verbose_level > 1:
                flag = '-vvv'

            kollacli_home = get_kollacli_home()
            command_string = 'sudo -u kolla ansible-playbook %s ' % flag
            inventory_string = '-i ' + os.path.join(kollacli_home,
                                                    'tools',
                                                    'json_generator.py ')
            playbook_string = ' ' + os.path.join(kollacli_home,
                                                 'ansible/stop.yml')
            envvar_string = ' --extra-vars "hosts="' + hostname + '"'
            cmd = command_string + inventory_string
            cmd = cmd + playbook_string + envvar_string
            print_output = False

            if self.app.options.verbose_level > 1:
                # log the ansible command
                self.log.debug('cmd:' + cmd)
                print_output = True

                if self.app.options.verbose_level > 2:
                    # log the inventory
                    dbg_gen = os.path.join(kollacli_home, 'tools',
                                           'json_generator.py ')
                    (inv, _) = \
                        subprocess.Popen(dbg_gen.split(' '),
                                         stdout=subprocess.PIPE,
                                         stderr=subprocess.PIPE).communicate()
                    self.log.debug(inv)

            err_flag, _ = run_cmd(cmd, print_output)
            if err_flag:
                raise Exception('stop failed')

            self.log.info('stop succeeded')
        except CommandError as e:
            raise e
        except Exception:
            raise Exception(traceback.format_exc())

