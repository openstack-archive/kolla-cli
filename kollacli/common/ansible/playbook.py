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

import kollacli.i18n as u

from kollacli.common.ansible.job import AnsibleJob
from kollacli.common.utils import get_admin_user
from kollacli.common.utils import get_ansible_command
from kollacli.common.utils import get_ansible_plugin_dir
from kollacli.common.utils import get_kolla_etc
from kollacli.common.utils import get_kolla_home

from kollacli.common.inventory import Inventory

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

    def run(self):
        try:
            self._check_for_plugin()
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

    def _check_for_plugin(self):
        """check that plug-in is properly installed"""
        pi_dir = get_ansible_plugin_dir()
        pi_path = os.path.join(pi_dir, 'kolla_callback.py')
        if not os.path.exists(pi_path):
            LOG.warning(u._('WARNING: kolla callback plug-in is missing. '
                            'Should be here: {path}\n').format(path=pi_path))
        else:
            ansible_cfg_path = os.path.join(
                get_kolla_home(), '.ansible.cfg')
            with open(ansible_cfg_path, 'r') as cfg:
                whitelist_ok = False
                for line in cfg:
                    if (line.startswith('callback_whitelist') and
                            'kolla_callback' in line):
                        whitelist_ok = True
                        break
            if not whitelist_ok:
                LOG.warning(u._('WARNING: kolla callback plug-in is not '
                                'whitelisted '
                                'in {path}\n').format(path=ansible_cfg_path))

    def _get_playbook_cmd(self, inventory_path):
        flag = ''
        # verbose levels: 1=not verbose, 2=more verbose
        if self.verbose_level > 1:
            flag = '-'
            for x in range(1, self.verbose_level):
                flag += 'v'

        ansible_cmd = get_ansible_command(playbook=True)
        admin_user = get_admin_user()
        cmd = '/usr/bin/sudo -u %s %s %s' % (admin_user, ansible_cmd, flag)

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
        return cmd

    def _make_temp_inventory(self):
        """Create temporary inventory file

        A temporary inventory is created so that a
        unique id can be assigned to the deployment. That
        id will used by the ansible callback to tag messages
        and status from deployments back to the kolla code.
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
