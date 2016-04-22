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
import kollacli.i18n as u

from kollacli.api.exceptions import InvalidArgument
from kollacli.api.job import Job
from kollacli.common.ansible import actions
from kollacli.common.inventory import Inventory
from kollacli.common.utils import check_arg
from kollacli.common.utils import safe_decode


class AsyncApi(object):

    def async_deploy(self, hostnames=[],
                     serial_flag=False, verbose_level=1):
        """Deploy.

        Deploy containers to hosts.

        :param hostnames: hosts to deploy to. If empty, then deploy to all.
        :type hostnames: list of strings
        :param serial_flag: if true, deploy will be done one host at a time
        :type serial_flag: boolean
        :param verbose_level: the higher the number, the more verbose
        :type verbose_level: integer
        :return: Job object
        :rtype: Job
        """
        check_arg(hostnames, u._('Host names'), list,
                  empty_ok=True, none_ok=True)
        check_arg(serial_flag, u._('Serial flag'), bool)
        check_arg(verbose_level, u._('Verbose level'), int)
        hostnames = safe_decode(hostnames)

        ansible_job = actions.deploy(hostnames,
                                     serial_flag, verbose_level)
        return Job(ansible_job)

    def async_upgrade(self, verbose_level=1):
        """Upgrade.

        :param verbose_level: the higher the number, the more verbose
        :type verbose_level: integer
        :return: Job object
        :rtype: Job

        Upgrade containers to new version specified by the property
        "openstack_release."
        """
        check_arg(verbose_level, u._('Verbose level'), int)
        ansible_job = actions.upgrade(verbose_level)
        return Job(ansible_job)

    def async_host_destroy(self, hostnames, destroy_type, verbose_level=1,
                           include_data=False):
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
        :return: Job object
        :rtype: Job

        """
        check_arg(hostnames, u._('Host names'), list)
        check_arg(destroy_type, u._('Destroy type'), str)
        check_arg(verbose_level, u._('Verbose level'), int)
        check_arg(include_data, u._('Include data'), bool)
        if destroy_type not in ['stop', 'kill']:
            raise InvalidArgument(
                u._('Invalid destroy type ({type}). Must be either '
                    '"stop" or "kill".').format(type=destroy_type))

        hostnames = safe_decode(hostnames)
        inventory = Inventory.load()
        inventory.validate_hostnames(hostnames)

        ansible_job = actions.destroy_hosts(hostnames, destroy_type,
                                            verbose_level, include_data)
        return Job(ansible_job)

    def async_host_precheck(self, hostnames, verbose_level=1):
        """Check pre-deployment configuration of hosts.

        Check if host is ready for a new deployment. This will fail if
        any of the hosts are not configured correctly or if they have
        already been deployed to.
        :param hostnames: host names
        :type hostnames: list
        :param verbose_level: the higher the number, the more verbose
        :type verbose_level: integer
        :return: Job object
        :rtype: Job
        """
        check_arg(hostnames, u._('Host names'), list)
        check_arg(verbose_level, u._('Verbose level'), int)
        hostnames = safe_decode(hostnames)
        inventory = Inventory.load()
        inventory.validate_hostnames(hostnames)

        ansible_job = actions.precheck(hostnames, verbose_level)
        return Job(ansible_job)
