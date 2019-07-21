# Copyright(c) 2016, Oracle and/or its affiliates.  All Rights Reserved.
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
import traceback

from kolla_cli.common.ansible.job import AnsibleJob
from kolla_cli.common.inventory import Inventory
from kolla_cli.common.utils import get_ansible_command
from kolla_cli.common.utils import get_kolla_etc

MYPY = False
if MYPY:
    from typing import List  # noqa


LOG = logging.getLogger(__name__)


class AnsiblePlaybook(object):
    playbook_path = ''
    extra_vars = ''
    include_passwords = True
    flush_cache = True
    print_output = True
    verbose_level = 0
    hosts = None  # type: List[str]
    groups = None  # type: List[str]
    services = None  # type: List[str]
    ignore_error_strings = None  # type: List[str]
    serial = False
    deploy_id = None  # type: str
    inventory = None  # type: Inventory
    local_only = False
    become_user = None  # type: str

    def run(self):
        try:
            if self.local_only:
                # Create a temporary local inventory with only localhost
                self.inventory = Inventory()
                self.inventory.set_deploy_mode(False)
                self.inventory.add_host('localhost')
            else:
                self.inventory = Inventory.load()
            inventory_path = self._make_temp_inventory()
            cmd = self._get_playbook_cmd(inventory_path)
            self._log_ansible_cmd(cmd, inventory_path)

            # create and run the job
            job = AnsibleJob(cmd, self.deploy_id,
                             self.print_output, inventory_path)
            job._ignore_error_strings = self.ignore_error_strings
            job.run()
            return job

        except Exception:
            raise Exception(traceback.format_exc())

    def _get_playbook_cmd(self, inventory_path):
        flag = ''
        # verbose levels: 1=not verbose, 2=more verbose
        if self.verbose_level > 1:
            flag = '-'
            for x in range(1, self.verbose_level):
                flag += 'v'

        ansible_cmd = get_ansible_command(playbook=True)
        cmd = '%s %s' % (ansible_cmd, flag)

        cmd += ' -i %s' % inventory_path

        if self.include_passwords:
            cmd += ' %s' % self._get_password_path()

        cmd += ' %s' % self.playbook_path

        if self.extra_vars or self.serial:
            extra_vars = ''
            if self.extra_vars:
                extra_vars = self.extra_vars
                if self.serial:
                    extra_vars += ' '
            if self.serial:
                extra_vars += 'serial_var=1'

            cmd += ' --extra-vars \"%s\"' % extra_vars

        if self.services:
            service_string = ''
            first = True
            for service in self.services:
                if not first:
                    service_string += ','
                else:
                    first = False
                service_string = service_string + service
            cmd += ' --tags %s' % service_string

        if self.hosts:
            host_string = ''
            first = True
            for host in self.hosts:
                if not first:
                    host_string += ','
                else:
                    first = False
                host_string = host_string + host
            cmd += ' --limit %s' % host_string

        if self.flush_cache:
            cmd += ' --flush-cache'

        if self.become_user:
            cmd += ' --become-user %s' % self.become_user

        return cmd

    def _make_temp_inventory(self):
        """Create temporary inventory file

        A temporary inventory is created so that a
        unique id can be assigned to the deployment.
        """
        inventory_filter = {}
        inventory_path = \
            self.inventory.create_json_gen_file(inventory_filter)

        # inv path = /tmp/kolla_UUID/temp_inventory.py
        deploy_id = os.path.dirname(inventory_path)
        self.deploy_id = deploy_id.split('kolla_')[1]

        return inventory_path

    def _get_password_path(self):
        kolla_etc = get_kolla_etc()
        return ('-e @' + os.path.join(kolla_etc, 'passwords.yml '))

    def _log_ansible_cmd(self, cmd, inventory_path):
        if self.verbose_level > 2:
            # log the ansible command
            LOG.debug('cmd:\n%s' % cmd)

            if self.verbose_level > 3:
                # log the inventory
                with open(inventory_path, 'r') as inv_file:
                    inv = inv_file.read()
                LOG.debug('\ninventory: \n%s' % inv)
