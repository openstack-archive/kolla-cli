# Copyright(c) 2019, caoyuan. All Rights Reserved.
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

from kolla_cli.api.exceptions import InvalidHosts
from kolla_cli.api.exceptions import InvalidServices
from kolla_cli.common.inventory import Inventory
import kolla_cli.i18n as u


def check_kolla_args(hostnames=[], servicenames=[]):

    if not any([hostnames, servicenames]):
        return

    inventory = Inventory.load()
    if hostnames:
        all_hosts = inventory.get_hostnames()
        invalid_hosts = list(set(hostnames) - set(all_hosts))
        if invalid_hosts:
            raise InvalidHosts(
                u._('Hosts {hosts} are not valid.').format(
                    hosts=invalid_hosts))

    if servicenames:
        all_services = [service.name
                        for service in inventory.get_services()]
        invalid_services = list(set(servicenames) - set(all_services))
        if invalid_services:
            raise InvalidServices(
                u._('Services {services} are not valid.').format(
                    services=invalid_services))
