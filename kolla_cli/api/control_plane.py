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

from kolla_cli.api.job import Job
from kolla_cli.common.ansible.actions import KollaAction
from kolla_cli.common.ansible.utils import check_kolla_args
from kolla_cli.common.inventory import Inventory
from kolla_cli.common.utils import check_arg
from kolla_cli.common.utils import safe_decode
import kolla_cli.i18n as u

MYPY = False
if MYPY:
    from typing import List  # noqa


class ControlPlaneApi(object):

    @staticmethod
    def deploy(hostnames=[],
               serial_flag=False, verbose_level=1, servicenames=[]):
        # type: (List[str], bool, int, List[str]) -> Job
        """Deploy.

        Deploy and start all kolla containers.

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

        check_kolla_args(hostnames=hostnames,
                         servicenames=servicenames)

        hostnames = safe_decode(hostnames)
        servicenames = safe_decode(servicenames)
        action = KollaAction(verbose_level=verbose_level,
                             playbook_name='site.yml')
        ansible_job = action.deploy(hostnames, serial_flag, servicenames)
        return Job(ansible_job)

    @staticmethod
    def prechecks(verbose_level=1, hostnames=[], servicenames=[]):
        # type: (int, List[str], List[str]) -> Job
        """Check pre-deployment configuration of hosts.

        Check if host is ready for a new deployment. This will fail if
        any of the hosts are not configured correctly or if they have
        already been deployed to.
        :param hostnames: host names
        :type hostnames: list
        :param verbose_level: the higher the number, the more verbose
        :type verbose_level: integer
        :param servicenames: services to prechecks.
        :type servicenames: list of strings
        :return: Job object
        :rtype: Job
        """
        check_arg(hostnames, u._('Host names'), list,
                  empty_ok=True, none_ok=True)
        check_arg(verbose_level, u._('Verbose level'), int)
        check_arg(servicenames, u._('Service names'), list,
                  empty_ok=True, none_ok=True)

        check_kolla_args(hostnames=hostnames,
                         servicenames=servicenames)

        hostnames = safe_decode(hostnames)
        servicenames = safe_decode(servicenames)
        action = KollaAction(verbose_level=verbose_level,
                             playbook_name='site.yml')
        ansible_job = action.precheck(hostnames, servicenames)
        return Job(ansible_job)

    @staticmethod
    def pull(verbose_level=1, hostnames=[], servicenames=[]):
        """Pull.

        Pull all images for containers (only pulls, no running container).

        :param verbose_level: the higher the number, the more verbose
        :param hostnames: hosts to pull to. If empty, then pull to all.
        :type hostnames: list of strings
        :type verbose_level: integer
        :param servicenames: services to pull. If empty, then pull all.
        :return: Job object
        :rtype: Job
        """
        check_arg(hostnames, u._('Host names'), list,
                  empty_ok=True, none_ok=True)
        check_arg(verbose_level, u._('Verbose level'), int)
        check_arg(servicenames, u._('Service names'), list,
                  empty_ok=True, none_ok=True)

        check_kolla_args(hostnames=hostnames,
                         servicenames=servicenames)

        hostnames = safe_decode(hostnames)
        servicenames = safe_decode(servicenames)
        action = KollaAction(verbose_level=verbose_level,
                             playbook_name='site.yml')
        ansible_job = action.pull(hostnames, servicenames)
        return Job(ansible_job)

    @staticmethod
    def stop(verbose_level=1, hostnames=[], servicenames=[]):
        # type: (int, List[str], List[str]) -> Job
        """Stop Hosts.

        Stops all kolla related docker containers on the specified hosts.

        :param hostnames: host names
        :type hostnames: list
        :param verbose_level: the higher the number, the more verbose
        :type verbose_level: integer
        :param servicenames: services to stop. If empty, then stop all.
        :type servicenames: list of strings
        :return: Job object
        :rtype: Job
        """
        check_arg(verbose_level, u._('Verbose level'), int)
        check_arg(hostnames, u._('Host names'), list,
                  empty_ok=True, none_ok=True)
        check_arg(servicenames, u._('Service names'), list,
                  empty_ok=True, none_ok=True)

        check_kolla_args(hostnames=hostnames,
                         servicenames=servicenames)

        hostnames = safe_decode(hostnames)
        servicenames = safe_decode(servicenames)
        action = KollaAction(verbose_level=verbose_level,
                             playbook_name='site.yml')
        ansible_job = action.stop(hostnames, servicenames)
        return Job(ansible_job)

    @staticmethod
    def upgrade(verbose_level=1, hostnames=[], servicenames=[]):
        # type: (int, List[str], List[str]) -> Job
        """Upgrade.

        Upgrades existing OpenStack Environment.

        :param verbose_level: the higher the number, the more verbose
        :type verbose_level: integer
        :param hostnames: hostnames to upgrade.
        :type hostnames: list of strings.
        :param servicenames: services to upgrade. If empty, then upgrade all.
        :type servicenames: list of strings
        :return: Job object
        :rtype: Job

        Upgrade containers to new version specified by the property
        "openstack_release."
        """
        check_arg(verbose_level, u._('Verbose level'), int)
        check_arg(hostnames, u._('Host names'), list,
                  empty_ok=True, none_ok=True)
        check_arg(servicenames, u._('Service names'), list,
                  empty_ok=True, none_ok=True)

        check_kolla_args(servicenames=servicenames)

        hostnames = safe_decode(hostnames)
        servicenames = safe_decode(servicenames)
        action = KollaAction(verbose_level=verbose_level,
                             playbook_name='site.yml')
        ansible_job = action.upgrade(hostnames, servicenames)
        return Job(ansible_job)

    @staticmethod
    def genconfig(verbose_level=1, hostnames=[], servicenames=[]):
        # type: (int, List[str], List[str]) -> Job
        """Genconfig.

        Generate configuration files for enabled OpenStack services.

        :param verbose_level: the higher the number, the more verbose
        :type verbose_level: integer
        :param servicenames: services to generate. If empty, then generate all.
        :type servicenames: list of strings
        :return: Job object
        :rtype: Job

        Upgrade containers to new version specified by the property
        "openstack_release."
        """
        check_arg(hostnames, u._('Host names'), list,
                  empty_ok=True, none_ok=True)
        check_arg(verbose_level, u._('Verbose level'), int)
        check_arg(servicenames, u._('Service names'), list,
                  empty_ok=True, none_ok=True)

        check_kolla_args(hostnames=hostnames,
                         servicenames=servicenames)

        hostnames = safe_decode(hostnames)
        servicenames = safe_decode(servicenames)
        action = KollaAction(verbose_level=verbose_level,
                             playbook_name='site.yml')
        ansible_job = action.genconfig(hostnames, servicenames)
        return Job(ansible_job)

    @staticmethod
    def check(verbose_level=1, hostnames=[], servicenames=[]):
        # type: (int, List[str], List[str]) -> Job
        """Do post-deployment smoke tests.

        :param hostnames: host names
        :type hostnames: list
        :param verbose_level: the higher the number, the more verbose
        :type verbose_level: integer
        :param servicenames: services to check. If empty, then check all.
        :type servicenames: list of strings
        :return: Job object
        :rtype: Job
        """
        check_arg(verbose_level, u._('Verbose level'), int)
        check_arg(hostnames, u._('Host names'), list,
                  empty_ok=True, none_ok=True)
        check_arg(servicenames, u._('Service names'), list,
                  empty_ok=True, none_ok=True)

        check_kolla_args(servicenames=servicenames)

        hostnames = safe_decode(hostnames)
        servicenames = safe_decode(servicenames)
        action = KollaAction(verbose_level=verbose_level,
                             playbook_name='site.yml')
        ansible_job = action.check(hostnames, servicenames)
        return Job(ansible_job)

    @staticmethod
    def postdeploy(verbose_level=1):
        """Post-Deploy.

        Do post deploy on deploy node.

        :param verbose_level: the higher the number, the more verbose
        :type verbose_level: integer
        :return: Job object
        :rtype: Job
        """
        check_arg(verbose_level, u._('Verbose level'), int)

        action = KollaAction(verbose_level=verbose_level,
                             playbook_name='post-deploy.yml')
        ansible_job = action.postdeploy()
        return Job(ansible_job)

    @staticmethod
    def reconfigure(verbose_level=1, hostnames=[], servicenames=[]):
        # type: (int, List[str], List[str]) -> Job
        """Reconfigure.

        Reconfigure OpenStack service.

        :param hostnames: host names
        :type hostnames: list
        :param verbose_level: the higher the number, the more verbose
        :type verbose_level: integer
        :param servicenames: services to prechecks.
        :type servicenames: list of strings
        :return: Job object
        :rtype: Job
        """
        check_arg(hostnames, u._('Host names'), list,
                  empty_ok=True, none_ok=True)
        check_arg(verbose_level, u._('Verbose level'), int)
        check_arg(servicenames, u._('Service names'), list,
                  empty_ok=True, none_ok=True)

        check_kolla_args(hostnames=hostnames,
                         servicenames=servicenames)

        hostnames = safe_decode(hostnames)
        servicenames = safe_decode(servicenames)

        check_kolla_args(hostnames=hostnames,
                         servicenames=servicenames)

        action = KollaAction(verbose_level=verbose_level,
                             playbook_name='site.yml')
        ansible_job = action.reconfigure(hostnames, servicenames)
        return Job(ansible_job)

    @staticmethod
    def set_deploy_mode(remote_mode):
        # type: (bool) -> None
        """Set deploy mode to either local or remote.

        Local indicates that the openstack deployment will be
        to the local host. Remote means that the deployment is
        executed via ssh.

        NOTE: local mode is not supported and should never be used
        in production environments.

        :param remote_mode: if remote mode is True deployment is done via ssh
        :type remote_mode: bool
        """
        check_arg(remote_mode, u._('Remote mode'), bool)
        inventory = Inventory.load()
        inventory.set_deploy_mode(remote_mode)
        Inventory.save(inventory)

    @staticmethod
    def get_deploy_mode():
        """Get deploy mode from either local or remote.

        Local indicates that the openstack deployment will be
        to the local host. Remote means that the deployment is
        executed via ssh.

        NOTE: local mode is not supported and should never be used
        in production environments.
        """
        inventory = Inventory.load()
        remote_mode = inventory.remote_mode
        deploy_mode = 'remote' if remote_mode else 'local'
        return deploy_mode
