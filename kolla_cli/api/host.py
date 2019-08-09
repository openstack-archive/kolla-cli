# Copyright(c) 2017, Oracle and/or its affiliates.  All Rights Reserved.
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

from copy import copy

from kolla_cli.api.exceptions import InvalidArgument
from kolla_cli.api.job import Job
from kolla_cli.common.ansible.actions import KollaAction
from kolla_cli.common.inventory import Inventory
from kolla_cli.common.utils import check_arg
from kolla_cli.common.utils import safe_decode
import kolla_cli.i18n as u


MYPY = False
if MYPY:
    from typing import Dict  # noqa
    from typing import List  # noqa


class HostApi(object):

    @staticmethod
    def host_add(hostnames):
        # type: (List[str]) -> None
        """Add hosts to the inventory

        :param hostnames: list of strings
        """
        check_arg(hostnames, u._('Host names'), list)
        hostnames = safe_decode(hostnames)

        inventory = Inventory.load()
        any_changed = False
        for hostname in hostnames:
            changed = inventory.add_host(hostname)
            if changed:
                any_changed = True
        if any_changed:
            Inventory.save(inventory)

    @staticmethod
    def host_remove(hostnames):
        # type: (List[str]) -> None
        """Remove hosts from the inventory

        :param hostnames: list of strings
        """
        check_arg(hostnames, u._('Host names'), list)
        hostnames = safe_decode(hostnames)

        inventory = Inventory.load()
        any_changed = False
        for hostname in hostnames:
            changed = inventory.remove_host(hostname)
            if changed:
                any_changed = True
        if any_changed:
            Inventory.save(inventory)

    @staticmethod
    def host_get_all():
        # type: () -> List[Host]
        """Get all hosts in the inventory

        :return: Hosts
        :rtype: list of Host objects
        """
        inventory = Inventory.load()
        hosts = []
        host_groups = inventory.get_host_groups()
        for hostname, groupnames in host_groups.items():
            hosts.append(Host(hostname, groupnames))
        return hosts

    @staticmethod
    def host_get(hostnames):
        # type: (List[str]) -> List[Host]
        """Get selected hosts in the inventory

        :param hostnames: list of strings
        :return: hosts
        :rtype: list of Host objects
        """
        check_arg(hostnames, u._('Host names'), list)
        hostnames = safe_decode(hostnames)
        inventory = Inventory.load()
        inventory.validate_hostnames(hostnames)

        hosts = []
        host_groups = inventory.get_host_groups()
        for hostname in hostnames:
            hosts.append(Host(hostname, host_groups[hostname]))
        return hosts

    @staticmethod
    def host_ssh_check(hostnames):
        # type: (List[str]) -> Dict[str,Dict[str,object]]
        """Check hosts for ssh connectivity

        Check status is a dictionary of form:
            - {hostname: {
              'success':<True|False>,
              'msg':message_string},
              ...
              }

        :param hostnames: list of strings
        :return: check status
        :rtype: dictionary
        """
        check_arg(hostnames, u._('Host names'), list)
        inventory = Inventory.load()
        hostnames = safe_decode(hostnames)
        inventory.validate_hostnames(hostnames)
        summary = inventory.ssh_check_hosts(hostnames)
        return summary

    @staticmethod
    def host_setup(hosts_info):
        # type: (Dict[str,Dict[str,object]]) -> None
        """Setup multiple hosts for ssh access

        hosts_info is a dictionary of form:
            - {hostname': {
              'password': password
              'uname': user_name},
              ...
              }

        The uname entry is optional.

        :param hosts_info: dictionary
        """
        check_arg(hosts_info, u._('Hosts info'), dict)
        inventory = Inventory.load()
        inventory.validate_hostnames(hosts_info.keys())
        inventory.setup_hosts(hosts_info)

    @staticmethod
    def host_destroy(hostnames, destroy_type, verbose_level=1,
                     include_data=False, remove_images=False):
        # type: (List[str], str, int, bool, bool) -> Job
        """Destroy Hosts.

        Stops and removes all kolla related docker containers on the
        specified hosts.

        :param hostnames: host names
        :type hostnames: list
        :param destroy_type: either 'kill' or 'stop'
        :type destroy_type: string
        :param verbose_level: the higher the number, the more verbose
        :type verbose_level: integer
        :param include_data: if true, destroy data containers too.
        :type include_data: boolean
        :param remove_images: if true, destroy will remove the docker images
        :type remove_images: boolean
        :return: Job object
        :rtype: Job
        """
        check_arg(hostnames, u._('Host names'), list)
        check_arg(destroy_type, u._('Destroy type'), str)
        check_arg(verbose_level, u._('Verbose level'), int)
        check_arg(include_data, u._('Include data'), bool)
        check_arg(remove_images, u._('Remove images'), bool)
        if destroy_type not in ['stop', 'kill']:
            raise InvalidArgument(
                u._('Invalid destroy type ({type}). Must be either '
                    '"stop" or "kill".').format(type=destroy_type))

        hostnames = safe_decode(hostnames)
        inventory = Inventory.load()
        inventory.validate_hostnames(hostnames)

        action = KollaAction(verbose_level=verbose_level,
                             playbook_name='destroy.yml')
        ansible_job = action.destroy_hosts(hostnames, destroy_type,
                                           include_data, remove_images)
        return Job(ansible_job)


class Host(object):
    """Host"""

    def __init__(self, hostname, groupnames=[]):
        # type: (str, List[str]) -> None
        self.name = hostname
        self._groupnames = groupnames

    def get_name(self):
        # type: () -> str
        """Get name

        :return: host name
        :rtype: string
        """
        return self.name

    def get_groups(self):
        # type: () -> List[str]
        """Get names of the groups associated with this host

        :return: group names
        :rtype: list of strings

        Note: If the groups associated with this host change after this
        host is fetched, the host must be re-fetched to reflect those
        changes.
        """
        return copy(self._groupnames)
