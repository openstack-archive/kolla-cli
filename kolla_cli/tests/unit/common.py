# Copyright (c) 2018 OpenStack Foundation
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
import testtools

from kolla_cli.api.group import Group
from kolla_cli.api.host import Host
from kolla_cli.api.service import Service
from kolla_cli.common.ansible.job import AnsibleJob
from kolla_cli import shell


class KollaCliUnitTest(testtools.TestCase):

    def run_cli_command(self, command_string):
        # return 0 if command succeeded, non-0 if failed
        args = command_string.split()
        return shell.main(args)

    def get_fake_job(self):
        return AnsibleJob(None, None, None, None)

    def get_fake_host(self, hostname='foo'):
        return Host(hostname)

    def get_fake_group(self, groupname='group1', servicenames=[],
                       hostnames=[]):
        return Group(groupname, servicenames, hostnames)

    def get_fake_service(self, servicename='service1', parentnames=[],
                         childnames=[], groupnames=[]):
        return Service(servicename, parentnames, childnames, groupnames)
