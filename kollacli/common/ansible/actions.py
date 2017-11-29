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

import kollacli.i18n as u

from kollacli.api.exceptions import InvalidArgument
from kollacli.api.exceptions import InvalidConfiguration
from kollacli.api.exceptions import NotInInventory
from kollacli.common.ansible.playbook import AnsiblePlaybook
from kollacli.common.inventory import Inventory
from kollacli.common.passwords import get_empty_password_values
from kollacli.common.properties import AnsibleProperties
from kollacli.common.utils import get_kolla_etc
from kollacli.common.utils import get_kolla_home
from kollacli.common.utils import is_string_true

LOG = logging.getLogger(__name__)


def destroy_hosts(hostnames, destroy_type,
                  verbose_level=1, include_data=False,
                  remove_images=False):
    '''destroy containers on a set of hosts.

    The containers on the specified hosts will be stopped
    or killed.
    '''
    playbook = AnsiblePlaybook()
    playbook_name = 'destroy.yml'

    LOG.info(u._LI('Please be patient as this may take a while.'))
    kolla_home = get_kolla_home()
    playbook.playbook_path = os.path.join(kolla_home,
                                          'ansible/' + playbook_name)

    # 'hosts' is defined as 'all' in the playbook yml code, but inventory
    # filtering will subset that down to the hosts in playbook.hosts.
    playbook.hosts = hostnames
    if remove_images:
        playbook.extra_vars = 'destroy_include_images=yes'
    if verbose_level <= 1:
        playbook.print_output = False
    playbook.verbose_level = verbose_level
    job = playbook.run()
    return job


def deploy(hostnames=[],
           serial_flag=False, verbose_level=1, servicenames=[]):
    playbook = AnsiblePlaybook()
    kolla_home = get_kolla_home()
    playbook.playbook_path = os.path.join(kolla_home,
                                          'ansible/site.yml')
    playbook.extra_vars = 'action=deploy'
    playbook.hosts = hostnames
    playbook.serial = serial_flag
    playbook.verbose_level = verbose_level
    playbook.services = servicenames

    _run_deploy_rules(playbook)

    job = playbook.run()
    return job


def precheck(hostnames, verbose_level=1):
    '''run check playbooks on a set of hosts'''
    playbook_name = 'prechecks_preinstall.yml'
    kolla_home = get_kolla_home()
    playbook = AnsiblePlaybook()
    playbook.playbook_path = os.path.join(kolla_home,
                                          'ansible/' + playbook_name)

    # define 'hosts' to be all, but inventory filtering will subset
    # that down to the hosts in playbook.hosts.
    playbook.extra_vars = 'hosts=all'
    playbook.hosts = hostnames
    playbook.print_output = True
    playbook.verbose_level = verbose_level

    job = playbook.run()
    return job


def pull(verbose_level=1):
    '''run pull action against all hosts'''
    playbook = AnsiblePlaybook()
    kolla_home = get_kolla_home()
    playbook.playbook_path = os.path.join(kolla_home,
                                          'ansible/site.yml')
    playbook.extra_vars = 'action=pull'
    playbook.verbose_level = verbose_level

    job = playbook.run()
    return job


def stop_hosts(hostnames=[], verbose_level=1):
    '''stop containers on a set of hosts.

    The containers on the specified hosts will be stopped
    or killed if the stop takes over 20 seconds.
    '''
    playbook = AnsiblePlaybook()
    playbook_name = 'stop.yml'
    LOG.info(u._LI('Please be patient as this may take a while.'))
    kolla_home = get_kolla_home()
    playbook.playbook_path = os.path.join(kolla_home,
                                          'ansible/' + playbook_name)

    # 'hosts' is defined as 'all' in the playbook yml code, but inventory
    # filtering will subset that down to the hosts in playbook.hosts.
    playbook.hosts = hostnames
    if verbose_level <= 1:
        playbook.print_output = False
    playbook.verbose_level = verbose_level
    job = playbook.run()
    return job


def reconfigure(verbose_level=1):
    playbook = AnsiblePlaybook()
    kolla_home = get_kolla_home()
    playbook.playbook_path = os.path.join(kolla_home,
                                          'ansible/site.yml')
    playbook.extra_vars = 'action=reconfigure'
    playbook.verbose_level = verbose_level

    _run_deploy_rules(playbook)

    job = playbook.run()
    return job


def upgrade(verbose_level=1, servicenames=[]):
    playbook = AnsiblePlaybook()
    kolla_home = get_kolla_home()
    playbook.playbook_path = os.path.join(kolla_home,
                                          'ansible/site.yml')
    playbook.extra_vars = 'action=upgrade'
    playbook.print_output = True
    playbook.verbose_level = verbose_level
    playbook.services = servicenames

    job = playbook.run()
    return job


def _run_deploy_rules(playbook):
    properties = AnsibleProperties()
    inventory = Inventory.load()

    # check that password file has no empty password values
    empty_keys = get_empty_password_values()
    if empty_keys:
        raise InvalidConfiguration(
            u._('Deploy failed. There are empty password values '
                'in {etc}passwords.yml. '
                'Please run kollacli password init or '
                'kollacli password set(key) to correct them. '
                '\nEmpty passwords: '
                '{keys}').format(etc=get_kolla_etc(), keys=empty_keys))

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
                    if _is_service_enabled(servicename, inventory, properties):
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

    # check that ring files are in /etc/kolla/config/swift if
    # swift is enabled
    expected_files = ['account.ring.gz',
                      'container.ring.gz',
                      'object.ring.gz']
    is_swift_enabled = _is_service_enabled('swift', inventory, properties)

    if is_swift_enabled:
        path_pre = os.path.join(get_kolla_etc(), 'config', 'swift')
        for expected_file in expected_files:
            path = os.path.join(path_pre, expected_file)
            if not os.path.isfile(path):
                msg = u._(
                    'Deploy failed. '
                    'Swift is enabled but ring buffers have '
                    'not yet been set up. Please see the '
                    'documentation for swift configuration '
                    'instructions.')
                raise InvalidConfiguration(msg)


def _is_service_enabled(servicename, inventory, properties):
    service = inventory.get_service(servicename)
    if service is not None:
        enabled_property = 'enable_' + servicename.replace('-', '_')
        is_enabled = properties.get_property_value(enabled_property)
        if type(is_enabled) is str:
            is_enabled = is_string_true(is_enabled)
    return is_enabled
