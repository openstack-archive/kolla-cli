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
import subprocess  # nosec
import traceback

import kollacli.i18n as u

from kollacli.common.utils import get_admin_user
from kollacli.common.utils import get_ansible_command
from kollacli.common.utils import get_kolla_etc
from kollacli.common.utils import run_cmd
from kollacli.exceptions import CommandError

from kollacli.common.inventory import Inventory


class AnsiblePlaybook(object):
    playbook_path = ''
    extra_vars = ''
    include_globals = True
    include_passwords = True
    flush_cache = True
    print_output = True
    verbose_level = 0
    hosts = None
    groups = None
    services = None
    serial = False

    log = logging.getLogger(__name__)

    def run(self):
        globals_string = None
        password_string = None
        inventory_path = None
        cmd = ''
        try:
            flag = ''
            # verbose levels: 1=not verbose, 2=more verbose
            if self.verbose_level > 1:
                flag = '-vvv'

            ansible_cmd = get_ansible_command(playbook=True)
            admin_user = get_admin_user()
            command_string = ('/usr/bin/sudo -u %s %s %s'
                              % (admin_user, ansible_cmd, flag))
            inventory_filter = {}
            inventory = Inventory.load()
            if self.hosts:
                for hostname in self.hosts:
                    host = inventory.get_host(hostname)
                    if not host:
                        raise CommandError(u._('Host ({host}) not found.')
                                           .format(host=hostname))
                inventory_filter['deploy_hosts'] = self.hosts
            elif self.groups:
                for groupname in self.groups:
                    group = inventory.get_group(groupname)
                    if not group:
                        raise CommandError(u._('Group ({group}) not found.')
                                           .format(group=groupname))
                inventory_filter['deploy_groups'] = self.groups

            inventory_path = \
                inventory.create_json_gen_file(inventory_filter)
            inventory_string = '-i ' + inventory_path
            cmd = (command_string + ' ' + inventory_string)

            if self.include_globals:
                globals_string = self._get_globals_path()
                cmd = (cmd + ' ' + globals_string)

            if self.include_passwords:
                password_string = self._get_password_path()
                cmd = (cmd + ' ' + password_string)

            cmd = (cmd + ' ' + self.playbook_path)

            if self.extra_vars or self.serial:
                extra_vars = ''
                if self.extra_vars:
                    extra_vars = self.extra_vars
                    if self.serial:
                        extra_vars += ' '
                if self.serial:
                    extra_vars += 'serial_var=1'

                cmd = (cmd + ' --extra-vars \"' +
                       extra_vars + '\"')

            if self.services:
                service_string = ''
                first = True
                for service in self.services:
                    valid_service = inventory.get_service(service)
                    if not valid_service:
                        raise CommandError(u._('Service ({srvc}) not found.')
                                           .format(srvc=service))
                    if not first:
                        service_string = service_string + ','
                    else:
                        first = False
                    service_string = service_string + service
                cmd = (cmd + ' --tags ' + service_string)

            if self.flush_cache:
                cmd = (cmd + ' --flush-cache')

            if self.verbose_level > 1:
                # log the ansible command
                self.log.debug('cmd:' + cmd)

                if self.verbose_level > 2:
                    # log the inventory
                    dbg_gen = inventory_path
                    (inv, _) = \
                        subprocess.Popen(dbg_gen.split(' '),  # nosec
                                         stdout=subprocess.PIPE,
                                         stderr=subprocess.PIPE).communicate()
                    self.log.debug(inv)

            err_msg, output = run_cmd(cmd, self.print_output)
            if err_msg:
                if not self.print_output:
                    # since the user didn't see the output, include it in
                    # the error message
                    err_msg = '%s %s' % (err_msg, output)
                raise CommandError(err_msg)

            self.log.info(u._('Success'))
        except CommandError as e:
            raise e
        except Exception:
            raise Exception(traceback.format_exc())
        finally:
            if inventory_path:
                os.remove(inventory_path)

    def _get_globals_path(self):
        kolla_etc = get_kolla_etc()
        return (' -e @' + os.path.join(kolla_etc, 'globals.yml '))

    def _get_password_path(self):
        kolla_etc = get_kolla_etc()
        return (' -e @' + os.path.join(kolla_etc, 'passwords.yml '))
