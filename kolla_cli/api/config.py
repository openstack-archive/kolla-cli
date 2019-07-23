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

from kolla_cli.api.exceptions import FailedOperation
from kolla_cli.api.exceptions import InvalidArgument
from kolla_cli.common.inventory import Inventory
from kolla_cli.common import utils
from kolla_cli.common.utils import check_arg
import kolla_cli.i18n as u


class ConfigApi(object):

    @staticmethod
    def config_reset():
        """Config Reset.

        Resets the kolla-ansible configuration to its release defaults.
        """
        actions_path = utils.get_kolla_actions_path()
        cmd = ('%s config_reset' % actions_path)
        err_msg, output = utils.run_cmd(cmd, print_output=False)
        if err_msg:
            raise FailedOperation(
                u._('Configuration reset failed. {error} {message}')
                .format(error=err_msg, message=output))

    def config_import_inventory(self, file_path):
        # type: (str) -> None
        """Config Import Inventory

        Import groups and child associations from the provided
        inventory file. This currently does not import hosts, group
        vars, or host vars that may also exist in the inventory file.

        :param file_path: path to inventory file to import
        :type file_path: string
        """
        check_arg(file_path, u._('File path'), str)
        if not os.path.isfile(file_path):
            raise InvalidArgument(
                u._('File {path} is not valid.').format(
                    path=file_path))
        inventory = Inventory(file_path)
        Inventory.save(inventory)
