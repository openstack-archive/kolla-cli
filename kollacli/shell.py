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
"""Command-line interface to Kolla"""
import logging
import os
import sys

from cliff.app import App
from cliff.commandmanager import CommandManager

import kollacli.i18n as u

from kollacli.api.client import ClientApi
from kollacli.commands.exceptions import CommandError
from kollacli.common.inventory import INVENTORY_PATH
from kollacli.common.utils import get_kollacli_etc

LOG = logging.getLogger(__name__)

VERSION = '4.0'


class KollaCli(App):
    def __init__(self):
        super(KollaCli, self).__init__(
            description=u._('Command-Line Client for OpenStack Kolla'),
            version=VERSION,
            command_manager=CommandManager('kolla.cli'),
            )

        inventory_path = os.path.join(get_kollacli_etc(),
                                      INVENTORY_PATH)
        if os.path.isfile(inventory_path) is False:
            err_string = u._(
                'Required file ({inventory}) does not exist.\n'
                'Please re-install the kollacli to '
                'recreate the file.').format(inventory=inventory_path)
            raise CommandError(err_string)

        # set up logging and test that user running shell is part
        # of kolla group
        ClientApi()

        # paramiko log is very chatty, tune it down
        logging.getLogger('paramiko').setLevel(logging.WARNING)

        self.dump_stack_trace = False


def main(argv=sys.argv[1:]):
    shell = KollaCli()
    return shell.run(argv)

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
