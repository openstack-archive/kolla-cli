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
import os

import kolla_cli.i18n as u

from kolla_cli.api.exceptions import FailedOperation
from kolla_cli.api.exceptions import InvalidArgument
from kolla_cli.common.inventory import Inventory
from kolla_cli.common import utils
from kolla_cli.common.utils import check_arg


class ConfigApi(object):

    @staticmethod
    def config_reset(inventory_path=None):
        # type: (str) -> None
        """Config Reset.

        Resets the kolla-ansible configuration to its release defaults. If
        an inventory path is provided, the inventory file will be imported
        after the reset,

        :param inventory_path: absolute path to inventory file to import
        :type inventory_path: string
        """
        if inventory_path:
            check_arg(inventory_path, u._('Inventory path'), str)
            if not os.path.isfile(inventory_path):
                raise InvalidArgument(
                    u._('Inventory file {path} is not valid.').format(
                        path=inventory_path))

        actions_path = utils.get_kolla_actions_path()
        cmd = ('%s config_reset' % actions_path)
        err_msg, output = utils.run_cmd(cmd, print_output=False)
        if err_msg:
            raise FailedOperation(
                u._('Configuration reset failed. {error} {message}')
                .format(error=err_msg, message=output))

        if inventory_path:
            inventory = Inventory(inventory_path)
            Inventory.save(inventory)
