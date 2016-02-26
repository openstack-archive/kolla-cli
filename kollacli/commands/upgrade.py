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
import traceback

from kollacli.common.ansible.actions import upgrade

from cliff.command import Command

LOG = logging.getLogger(__name__)


class Upgrade(Command):
    """Upgrade."""
    def get_parser(self, prog_name):
        parser = super(Upgrade, self).get_parser(prog_name)
        return parser

    def take_action(self, parsed_args):
        verbose_level = self.app.options.verbose_level
        try:
            upgrade(verbose_level)

        except Exception:
            raise Exception(traceback.format_exc())
