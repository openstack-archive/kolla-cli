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

import kollacli.i18n as u

from kollacli.common.ansible.playbook import AnsiblePlaybook
from kollacli.common import properties
from kollacli.common.properties import AnsibleProperties
from kollacli.common.utils import get_kolla_etc
from kollacli.common.utils import get_kolla_home
from kollacli.common.utils import get_kollacli_home
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
    playbook.print_output = False
    playbook.verbose_level = verbose_level
    playbook.run()


def deploy(hostnames=[], groupnames=[], servicenames=[],
           serial_flag=False, verbose_level=1):
    if hostnames and groupnames:
        raise CommandError(
            u._('Hosts and Groups arguments cannot '
                'both be present at the same time.'))

    _run_deploy_rules()

    playbook = AnsiblePlaybook()
    kolla_home = get_kolla_home()
    playbook.playbook_path = os.path.join(kolla_home,
                                          'ansible/site.yml')
    playbook.hosts = hostnames
    playbook.groups = groupnames
    playbook.services = servicenames
    playbook.serial = serial_flag

    playbook.verbose_level = verbose_level
    playbook.run()


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
    playbook.run()


def _run_deploy_rules():
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
                msg = u._(
                    'Deploy failed. '
                    'Swift is enabled but ring buffers have '
                    'not yet been set up. Please see the '
                    'documentation for swift configuration '
                    'instructions.')
                raise CommandError(msg)
