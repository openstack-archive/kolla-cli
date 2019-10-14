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

from kolla_cli.api.exceptions import InvalidArgument
from kolla_cli.api.exceptions import InvalidConfiguration
from kolla_cli.api.exceptions import NotInInventory
from kolla_cli.common.ansible.playbook import AnsiblePlaybook
from kolla_cli.common.inventory import Inventory
from kolla_cli.common.passwords import get_empty_password_values
from kolla_cli.common.properties import AnsibleProperties
from kolla_cli.common.utils import get_admin_user
from kolla_cli.common.utils import get_kolla_ansible_home
from kolla_cli.common.utils import get_kolla_etc
from kolla_cli.common.utils import is_string_true
import kolla_cli.i18n as u

LOG = logging.getLogger(__name__)


class KollaAction(object):
    """Kolla Action."""

    def __init__(self, verbose_level=0, playbook_name=''):
        self.playbook_name = playbook_name
        self.playbook_path = os.path.join(get_kolla_ansible_home(),
                                          'ansible/',
                                          self.playbook_name)
        self.playbook = AnsiblePlaybook()
        self.playbook.verbose_level = verbose_level
        self.playbook.playbook_path = self.playbook_path

    def certificate_init(self):
        '''Creates a self-signed certificate'''

        self.playbook.local_only = True
        self.playbook.become_user = get_admin_user()
        job = self.playbook.run()
        return job

    def deploy(self, hostnames=[], serial_flag=False, servicenames=[]):
        '''Deploy and start all kolla containers.'''

        self.playbook.hosts = hostnames
        self.playbook.serial = serial_flag
        self.playbook.services = servicenames
        self.playbook.extra_vars = 'kolla_action=deploy'

        self._run_deploy_rules(self.playbook)

        job = self.playbook.run()
        return job

    def reconfigure(self, hostnames=[], servicenames=[]):
        '''Reconfigure OpenStack service.'''

        self.playbook.hosts = hostnames
        self.playbook.services = servicenames
        self.playbook.extra_vars = 'kolla_action=reconfigure'

        self._run_deploy_rules(self.playbook)

        job = self.playbook.run()
        return job

    def postdeploy(self):
        '''Do post deploy on deploy node.'''

        self.playbook.local_only = True
        self.playbook.become_user = get_admin_user()
        job = self.playbook.run()
        return job

    def destroy_hosts(self, hostnames, destroy_type,
                      include_data=False, remove_images=False):
        '''destroy containers on a set of hosts.

        The containers on the specified hosts will be stopped
        or killed.
        '''

        LOG.info(u._LI('Please be patient as this may take a while.'))
        # 'hosts' is defined as 'all' in the playbook yml code, but inventory
        # filtering will subset that down to the hosts in playbook.hosts.
        self.playbook.hosts = hostnames
        if remove_images:
            self.playbook.extra_vars = 'destroy_include_images=yes'
        if self.playbook.verbose_level <= 1:
            self.playbook.print_output = False
        job = self.playbook.run()
        return job

    def stop(self, hostnames=[], servicenames=[]):
        '''stop containers on a set of hosts.

        The containers on the specified hosts will be stopped
        or killed if the stop takes over 20 seconds.
        '''

        LOG.info(u._LI('Please be patient as this may take a while.'))
        # 'hosts' is defined as 'all' in the playbook yml code, but inventory
        # filtering will subset that down to the hosts in playbook.hosts.
        self.playbook.hosts = hostnames
        self.playbook.services = servicenames
        self.playbook.extra_vars = 'kolla_action=stop'
        if self.playbook.verbose_level <= 1:
            self.playbook.print_output = False
        job = self.playbook.run()
        return job

    def precheck(self, hostnames=[], servicenames=[]):
        '''run check playbooks on a set of hosts'''

        # check that password file has no empty password values
        empty_keys = get_empty_password_values()
        if empty_keys:
            raise InvalidConfiguration(
                u._('password check failed. There are empty password values '
                    'in {etc}passwords.yml. '
                    'Please run kolla-cli password init or '
                    'kolla-cli password set(key) to correct them. '
                    '\nEmpty passwords: '
                    '{keys}').format(etc=get_kolla_etc(), keys=empty_keys))

        # define 'hosts' to be all, but inventory filtering will subset
        # that down to the hosts in playbook.hosts.
        self.playbook.hosts = hostnames
        self.playbook.services = servicenames
        self.playbook.extra_vars = 'kolla_action=precheck'
        self.playbook.print_output = True
        job = self.playbook.run()
        return job

    def pull(self, hostnames=[], servicenames=[]):
        '''run pull action against all hosts'''

        self.playbook.hosts = hostnames
        self.playbook.services = servicenames
        self.playbook.extra_vars = 'kolla_action=pull'
        self.playbook.print_output = True
        job = self.playbook.run()
        return job

    def upgrade(self, hostnames=[], servicenames=[]):
        '''Upgrades existing OpenStack Environment.'''

        self.playbook.hosts = hostnames
        self.playbook.services = servicenames
        self.playbook.extra_vars = 'kolla_action=upgrade'
        self.playbook.print_output = True
        job = self.playbook.run()
        return job

    def genconfig(self, hostnames=[], servicenames=[]):
        '''Generate configuration files for enabled OpenStack services'''

        self.playbook.hosts = hostnames
        self.playbook.services = servicenames
        self.playbook.extra_vars = 'kolla_action=config'
        self.playbook.print_output = True
        job = self.playbook.run()
        return job

    def check(self, hostnames=[], servicenames=[]):
        '''Do post-deployment smoke tests.'''

        self.playbook.hosts = hostnames
        self.playbook.services = servicenames
        self.playbook.extra_vars = 'kolla_action=check'
        self.playbook.print_output = True
        job = self.playbook.run()
        return job

    def _run_deploy_rules(self, playbook):
        properties = AnsibleProperties()
        inventory = Inventory.load()

        # cannot have both groups and hosts
        if playbook.hosts and playbook.groups:
            raise InvalidArgument(
                u._('Hosts and Groups arguments cannot '
                    'both be present at the same time.'))

        # verify that all services exists
        if playbook.services:
            for service in playbook.services:
                valid_service = inventory.get_service(service)
                if not valid_service:
                    raise NotInInventory(u._('Service'), service)

        # check that every group with enabled services
        # has hosts associated to it
        group_services = inventory.get_group_services()
        failed_groups = []
        failed_services = []
        if group_services:
            for (groupname, servicenames) in group_services.items():
                group = inventory.get_group(groupname)
                hosts = group.get_hostnames()

                group_needs_host = False
                if not hosts:
                    for servicename in servicenames:
                        if self._is_service_enabled(servicename,
                                                    inventory,
                                                    properties):
                            group_needs_host = True
                            failed_services.append(servicename)
                    if group_needs_host:
                        failed_groups.append(groupname)

            if len(failed_groups) > 0:
                raise InvalidConfiguration(
                    u._('Deploy failed. '
                        'Groups: {groups} with enabled '
                        'services : {services} '
                        'have no associated hosts')
                    .format(groups=failed_groups, services=failed_services))

    def _is_service_enabled(self, servicename, inventory, properties):
        service = inventory.get_service(servicename)
        if service is not None:
            enabled_property = 'enable_' + servicename.replace('-', '_')
            is_enabled = properties.get_property_value(enabled_property)
            if type(is_enabled) is str:
                is_enabled = is_string_true(is_enabled)
        return is_enabled
