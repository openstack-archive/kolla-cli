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
from kollacli.ansible.properties import AnsibleProperties
from kollacli.exceptions import CommandError
from kollacli.i18n import _
from kollacli.utils import get_admin_user
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
        self._run_rules()
        try:
            flag = ''
            # verbose levels: 1=not verbose, 2=more verbose
            if self.app.options.verbose_level > 1:
                flag = '-vvv'

            kollacli_home = get_kollacli_home()
            kolla_home = get_kolla_home()
            kolla_etc = get_kolla_etc()
            admin_user = get_admin_user()
            command_string = ('sudo -u %s ansible-playbook %s '
                              % (admin_user, flag))
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

    def _run_rules(self):
        # check that ring files are in /etc/kolla/config/swift if
        # swift is enabled
        expected_files = ['account.ring.gz',
                          'container.ring.gz',
                          'object.ring.gz']
        properties = AnsibleProperties()
        is_enabled = properties.get_property('enable_swift')
        if is_enabled == 'yes':
            path_pre = os.path.join(get_kolla_etc(), 'config', 'swift')
            for expected_file in expected_files:
                path = os.path.join(path_pre, expected_file)
                if not os.path.isfile(path):
                    msg = ('Deploy failed. ' +
                           'Swift is enabled but ring buffers have ' +
                           'not yet been set up. Please see the ' +
                           'documentation for swift configuration ' +
                           'instructions.')
                    raise CommandError(msg)


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
            kolla_templates = os.path.join(kolla_home, 'templates')
            kolla_etc = get_kolla_etc()
            kolla_config = os.path.join(kolla_etc, 'config')
            kolla_globals = os.path.join(kolla_etc, 'globals.yml')
            kollacli_etc = get_kollacli_etc()
            ketc = 'kolla/etc/'
            kshare = 'kolla/share/'
            fd, dump_path = tempfile.mkstemp(prefix='kollacli_dump_',
                                             suffix='.tgz')
            os.close(fd)  # avoid fd leak
            with tarfile.open(dump_path, 'w:gz') as tar:
                # Can't blanket add kolla_home because the .ssh dir is
                # accessible by the kolla user only (not kolla group)
                tar.add(kolla_ansible,
                        arcname=ketc + os.path.basename(kolla_ansible))
                tar.add(kolla_docs,
                        arcname=ketc + os.path.basename(kolla_docs))
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
                self._get_cli_list_info(tar)
            self.log.info('dump successful to %s' % dump_path)
        except Exception:
            raise Exception(traceback.format_exc())

    def _get_cli_list_info(self, tar):
        fd, path = tempfile.mkstemp(suffix='.tmp')
        os.close(fd)
        with open(path, 'w') as tmp_file:
            cmds = ['service listgroups',
                    'service list',
                    'group listservices',
                    'group listhosts',
                    'host list',
                    'property list',
                    'password list']
            for cmd in cmds:
                _, output = run_cmd('kollacli ' + cmd, False)
                tmp_file.write('\n\n$ %s\n' % cmd)
                for line in output:
                    tmp_file.write(line + '\n')

        tar.add(path, arcname=os.path.join('kolla', 'cli_list_output'))
        os.remove(path)
        return


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
