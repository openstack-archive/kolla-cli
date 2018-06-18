# Copyright(c) 2018, Oracle and/or its affiliates.  All Rights Reserved.
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
import traceback

import kolla_cli.i18n as u

from cliff.command import Command

from kolla_cli.api.client import ClientApi

CLIENT = ClientApi()
LOG = logging.getLogger(__name__)


class ConfigReset(Command):
    """Resets the kolla-ansible configuration

    The properties and inventory will be reset to their original
    values. If an inventory path is provided, the groups,
    hosts, and host vars in the provided inventory file will be
    imported into the kolla-cli inventory file.
    """

    def get_parser(self, prog_name):
        parser = super(ConfigReset, self).get_parser(prog_name)
        parser.add_argument('--inventory', nargs='?',
                            metavar='<inventory>',
                            help=u._('Path to inventory file'))
        return parser

    def take_action(self, parsed_args):
        try:
            inventory_path = None
            if parsed_args.inventory:
                inventory_path = parsed_args.inventory.strip()
            CLIENT.config_reset(inventory_path)
        except Exception:
            raise Exception(traceback.format_exc())
