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

from kolla_cli.common.inventory import Inventory


def check_kolla_args(hostnames=[], servicenames=[]):

    if not any([hostnames, servicenames]):
        return

    inventory = Inventory.load()
    if hostnames:
        inventory.validate_hostnames(hostnames)

    if servicenames:
        inventory.validate_servicenames(servicenames)
