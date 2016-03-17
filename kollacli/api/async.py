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

from kollacli.api.job import Job
from kollacli.common.ansible import actions

LOG = logging.getLogger(__name__)


class AsyncApi(object):

    # TODO(bmace) -- update this to only take host names
    # and we will probably only support compute host individual deploys
    def async_deploy(self, hostnames=[], groupnames=[], servicenames=[],
                     serial_flag=False, verbose_level=1):
        """Deploy.

        Deploy containers to hosts.
        """
        ansible_job = actions.deploy(hostnames, groupnames, servicenames,
                                     serial_flag, verbose_level)
        return Job(ansible_job)

    def async_upgrade(self, verbose_level=1):
        """Upgrade.

        Upgrade containers to new version specified by the property
        "openstack_release."
        """
        ansible_job = actions.upgrade(verbose_level)
        return Job(ansible_job)

    def async_host_destroy(self, hostname, destroy_type, verbose_level=1,
                           include_data=False):
        """Destroy Hosts.

        Stops and removes all kolla related docker containers on either the
        specified host or all hosts if hostname is "all".
        """
        ansible_job = actions.destroy_hosts(hostname, destroy_type,
                                            verbose_level, include_data)
        return Job(ansible_job)

    def async_host_precheck(self, hostname, verbose_level=1):
        """Check pre-deployment configuration of host(s).

        Check if host is ready for a new deployment. This will fail if
        the host is not configured correctly or if it has already been
        deployed to.

        If hostname is "all", then check all hosts.
        """
        ansible_job = actions.precheck(hostname, verbose_level)
        return Job(ansible_job)
