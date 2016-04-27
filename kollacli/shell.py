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
import sys

from cliff.app import App
from cliff.commandmanager import CommandManager

import kollacli.i18n as u

from kollacli.api.client import ClientApi

LOG = logging.getLogger(__name__)


class KollaCli(App):
    def __init__(self):
        super(KollaCli, self).__init__(
            description=u._('Command-Line Client for OpenStack Kolla'),
            version='0.2',
            command_manager=CommandManager('kolla.cli'),
            )

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
