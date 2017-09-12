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
import kollacli.i18n as u

from kollacli.api.job import Job
from kollacli.common.ansible import actions
from kollacli.common.inventory import Inventory
from kollacli.common.utils import check_arg
from kollacli.common.utils import safe_decode


class ControlPlaneApi(object):

    @staticmethod
    def deploy(hostnames=[],
               serial_flag=False, verbose_level=1, servicenames=[]):
        # type: (List[str], bool, int, List[str]) -> Job
        """Deploy.

        Deploy containers to hosts.

        :param hostnames: hosts to deploy to. If empty, then deploy to all.
        :type hostnames: list of strings
        :param serial_flag: if true, deploy will be done one host at a time
        :type serial_flag: boolean
        :param verbose_level: the higher the number, the more verbose
        :type verbose_level: integer
        :param servicenames: services to deploy. If empty, then deploy all.
        :type servicenames: list of strings
        :return: Job object
        :rtype: Job
        """
        check_arg(hostnames, u._('Host names'), list,
                  empty_ok=True, none_ok=True)
        check_arg(serial_flag, u._('Serial flag'), bool)
        check_arg(verbose_level, u._('Verbose level'), int)
        check_arg(servicenames, u._('Service names'), list,
                  empty_ok=True, none_ok=True)
        hostnames = safe_decode(hostnames)
        servicenames = safe_decode(servicenames)

        ansible_job = actions.deploy(hostnames,
                                     serial_flag, verbose_level, servicenames)
        return Job(ansible_job)

    @staticmethod
    def pull(verbose_level=1):
        """Pull.

        Pull container images onto appropriate hosts.

        :param verbose_level: the higher the number, the more verbose
        :type verbose_level: integer
        :return: Job object
        :rtype: Job
        """
        check_arg(verbose_level, u._('Verbose level'), int)
        ansible_job = actions.pull(verbose_level)
        return Job(ansible_job)

    @staticmethod
    def upgrade(verbose_level=1, servicenames=[]):
        # type: (int, List[str]) -> Job
        """Upgrade.

        :param verbose_level: the higher the number, the more verbose
        :type verbose_level: integer
        :param servicenames: services to upgrade. If empty, then upgrade all.
        :type servicenames: list of strings
        :return: Job object
        :rtype: Job

        Upgrade containers to new version specified by the property
        "openstack_release."
        """
        check_arg(verbose_level, u._('Verbose level'), int)
        check_arg(servicenames, u._('Service names'), list,
                  empty_ok=True, none_ok=True)
        servicenames = safe_decode(servicenames)

        ansible_job = actions.upgrade(verbose_level, servicenames)
        return Job(ansible_job)

    @staticmethod
    def reconfigure(verbose_level=1):
        # type: (int) -> Job
        """Reconfigure.

        Reconfigure containers on hosts.

        :param verbose_level: the higher the number, the more verbose
        :type verbose_level: integer
        :return: Job object
        :rtype: Job
        """
        check_arg(verbose_level, u._('Verbose level'), int)

        ansible_job = actions.reconfigure(verbose_level)
        return Job(ansible_job)

    @staticmethod
    def set_deploy_mode(remote_mode):
        # type: (bool) -> None
        """Set deploy mode.

        Set deploy mode to either local or remote. Local indicates
        that the openstack deployment will be to the local host.
        Remote means that the deployment is executed via ssh.

        NOTE: local mode is not supported and should never be used
        in production environments.

        :param remote_mode: if remote mode is True deployment is done via ssh
        :type remote_mode: bool
        """
        check_arg(remote_mode, u._('Remote mode'), bool)
        inventory = Inventory.load()
        inventory.set_deploy_mode(remote_mode)
        Inventory.save(inventory)
