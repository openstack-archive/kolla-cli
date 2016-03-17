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

from kollacli.common.ansible.playbook import AnsiblePlaybook
from kollacli.common.inventory import Inventory
from kollacli.common import properties
from kollacli.common.properties import AnsibleProperties
from kollacli.common.utils import get_kolla_etc
from kollacli.common.utils import get_kolla_home
from kollacli.common.utils import get_kollacli_home
from kollacli.common.utils import is_string_true
from kollacli.exceptions import CommandError

LOG = logging.getLogger(__name__)


def destroy_hosts(hostname, destroy_type, verbose_level=1, include_data=False):
    '''destroy containers on a host (or all hosts).

    If hostname == 'all', then containers on all hosts will be
    stopped. Otherwise, the containers on the specified host
    will be stopped.

    The destroy type can either be 'stop' or 'kill'.
    '''
    if destroy_type not in ['stop', 'kill']:
        raise CommandError(
            u._('Invalid destroy type ({type}). Must be either '
                '"stop" or "kill".').format(type=destroy_type))

    playbook_name = 'host_destroy_no_data.yml'
    if include_data:
        playbook_name = 'host_destroy.yml'

    LOG.info(u._LI('Please be patient as this may take a while.'))
    ansible_properties = properties.AnsibleProperties()
    base_distro = \
        ansible_properties.get_property('kolla_base_distro')
    install_type = \
        ansible_properties.get_property('kolla_install_type')
    container_prefix = base_distro + '-' + install_type
    kollacli_home = get_kollacli_home()
    playbook = AnsiblePlaybook()
    playbook.playbook_path = os.path.join(kollacli_home,
                                          'ansible/' + playbook_name)
    playbook.extra_vars = 'hosts=' + hostname + \
                          ' prefix=' + container_prefix + \
                          ' destroy_type=' + destroy_type
    if verbose_level <= 1:
        playbook.print_output = False
    playbook.verbose_level = verbose_level
    job = playbook.run()
    return job


def deploy(hostnames=[], groupnames=[], servicenames=[],
           serial_flag=False, verbose_level=1):
    playbook = AnsiblePlaybook()
    kolla_home = get_kolla_home()
    playbook.playbook_path = os.path.join(kolla_home,
                                          'ansible/site.yml')
    playbook.hosts = hostnames
    playbook.groups = groupnames
    playbook.services = servicenames
    playbook.serial = serial_flag

    playbook.verbose_level = verbose_level

    _run_deploy_rules(playbook)

    job = playbook.run()
    return job


def precheck(hostname, verbose_level=1):
    '''run check playbooks on a host (or all hosts).

    If hostname == 'all', then checks will be run on all hosts,
    otherwise the check will only be run on the specified host.
    '''
    playbook_name = 'prechecks.yml'
    kolla_home = get_kolla_home()
    playbook = AnsiblePlaybook()
    playbook.playbook_path = os.path.join(kolla_home,
                                          'ansible/' + playbook_name)
    playbook.extra_vars = 'hosts=' + hostname
    playbook.print_output = True
    playbook.verbose_level = verbose_level
    job = playbook.run()
    return job


def upgrade(verbose_level=1):
    playbook = AnsiblePlaybook()
    kolla_home = get_kolla_home()
    playbook.playbook_path = os.path.join(kolla_home,
                                          'ansible/site.yml')
    playbook.extra_vars = 'action=upgrade'
    playbook.print_output = True
    playbook.verbose_level = verbose_level
    job = playbook.run()
    return job


def _run_deploy_rules(playbook):
    properties = AnsibleProperties()
    inventory = Inventory.load()

    # cannot have both groups and hosts
    if playbook.hosts and playbook.groups:
        raise CommandError(
            u._('Hosts and Groups arguments cannot '
                'both be present at the same time.'))

    # verify that all services exists
    if playbook.services:
        for service in playbook.services:
            valid_service = inventory.get_service(service)
            if not valid_service:
                raise CommandError(u._('Service ({srvc}) not found.')
                                   .format(srvc=service))

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
                for service in servicenames:
                    # check service enablement
                    enabled_property = 'enable_' + service.replace('-', '_')
                    is_enabled = properties.get_property(enabled_property)
                    if is_string_true(is_enabled):
                        group_needs_host = True
                        failed_services.append(service)
                if group_needs_host:
                    failed_groups.append(groupname)

        if len(failed_groups) > 0:
            raise CommandError(
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
    is_enabled = properties.get_property('enable_swift')
    if is_string_true(is_enabled):
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
                raise CommandError(msg)
