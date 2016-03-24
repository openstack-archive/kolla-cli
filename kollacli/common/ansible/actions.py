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
from kollacli.common import properties
from kollacli.common.properties import AnsibleProperties
from kollacli.common.utils import get_kolla_etc
from kollacli.common.utils import get_kolla_home
from kollacli.common.utils import get_kollacli_home
from kollacli.common.utils import is_string_true

LOG = logging.getLogger(__name__)


def destroy_hosts(hostnames, destroy_type,
                  verbose_level=1, include_data=False):
    '''destroy containers on a set of hosts.

    The containers on the specified hosts will be stopped
    or killed. That will be determined by the destroy_type,
    which can either be 'stop' or 'kill'.
    '''
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

    # 'hosts' is defined as 'all' in the playbook yml code, but inventory
    # filtering will subset that down to the hosts in playbook.hosts.
    playbook.extra_vars = 'prefix=' + container_prefix + \
                          ' destroy_type=' + destroy_type
    playbook.hosts = hostnames
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


def precheck(hostnames, verbose_level=1):
    '''run check playbooks on a set of hosts'''
    playbook_name = 'prechecks.yml'
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
<<<<<<< HEAD
                raise InvalidConfiguration(msg)
=======
                raise CommandError(msg)


def _is_service_enabled(servicename, inventory, properties):
    service_enabled = False
    service = None

    sub_service = inventory.get_sub_service(servicename)
    if sub_service is not None:
        enabled_property = 'enable_' + servicename.replace('-', '_')
        is_enabled = properties.get_property(enabled_property)
        if is_string_true(is_enabled):
            service_enabled = True

    # Only bother looking at the parent service if the sub service
    # is enabled.
    if service_enabled:
        servicename = sub_service.get_parent_service_name()
        if servicename is None:
            servicename = _find_parent_service(sub_service.name, inventory)

        service = inventory.get_service(servicename)
        if service is not None:
            enabled_property = 'enable_' + servicename.replace('-', '_')
            is_enabled = properties.get_property(enabled_property)
            if is_string_true(is_enabled):
                service_enabled = True
            else:
                service_enabled = False

    return service_enabled


def _find_parent_service(servicename, inventory):
    services = inventory.get_services()
    for service in services:
        sub_servicenames = service.get_sub_servicenames()
        for sub_servicename in sub_servicenames:
            if sub_servicename == servicename:
                return service.name
    return None
>>>>>>> 82cbb04... Added code to check sub-service parent enablement to determine if a group needs hosts
