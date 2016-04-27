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
from blaze.api.host import HostApi as BlazeHostApi
from kollacli.common.utils import reraise


class HostApi(object):

    class Host(object):
        """Host"""
        def __init__(self, hostname, groupnames):
            self.host = BlazeHostApi.Host(hostname, groupnames)
            self.name = hostname

        def get_name(self):
            """Get name

            :return: host name
            :rtype: string
            """
            return self.name

        def get_groups(self):
            """Get names of the groups associated with this host

            :return: group names
            :rtype: list of strings
            """
            return self.host.get_groups()

    def host_add(self, hostnames):
        """Add hosts to the inventory

        :param hostnames: list of strings
        """
        try:
            BlazeHostApi().host_add(hostnames)
        except Exception as e:
            reraise(e)

    def host_remove(self, hostnames):
        """Remove hosts from the inventory

        :param hostnames: list of strings
        """
        try:
            BlazeHostApi().host_remove(hostnames)
        except Exception as e:
            reraise(e)

    def host_get_all(self):
        """Get all hosts in the inventory

        :return: Hosts
        :rtype: Host
        """
        try:
            hosts = BlazeHostApi().host_get_all()
            new_hosts = []
            for host in hosts:
                new_host = self.Host(host.name, host.get_groups())
                new_hosts.append(new_host)
            return new_hosts
        except Exception as e:
            reraise(e)

    def host_get(self, hostnames):
        """Get selected hosts in the inventory

        :param hostnames: list of strings
        :return: hosts
        :rtype: Host
        """
        try:
            hosts = BlazeHostApi().host_get(hostnames)
            new_hosts = []
            for host in hosts:
                new_host = self.Host(host.name, host.get_groups())
                new_hosts.append(new_host)
            return new_hosts
        except Exception as e:
            reraise(e)

    def host_ssh_check(self, hostnames):
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
        try:
            return BlazeHostApi().host_ssh_check(hostnames)
        except Exception as e:
            reraise(e)

    def host_setup(self, hosts_info):
        """Setup multiple hosts for ssh access

        hosts_info is a dictionary of form:
        {hostname': {
            'password': password
            'uname': user_name},
         ...
        }
        The uname entry is optional.

        :param hosts_info: dictionary
        """
        try:
            BlazeHostApi().host_setup(hosts_info)
        except Exception as e:
            reraise(e)
