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

from cliff.command import Command

from kolla_cli.api.client import ClientApi
from kolla_cli.commands.exceptions import CommandError
import kolla_cli.i18n as u

CLIENT = ClientApi()
LOG = logging.getLogger(__name__)


class ConfigReset(Command):
    """Resets the kolla-ansible configuration to its release defaults."""

    def take_action(self, parsed_args):
        try:
            CLIENT.config_reset()
        except Exception:
            raise Exception(traceback.format_exc())


class ConfigImport(Command):
    """Config Import

    """
    def get_parser(self, prog_name):
        parser = super(ConfigImport, self).get_parser(prog_name)
        parser.add_argument('import_type', metavar='<import_type>',
                            help=u._('Import type=<inventory>'))
        parser.add_argument('file_path', metavar='<file_path>',
                            help=u._('File path'))
        return parser

    def take_action(self, parsed_args):
        try:
            legal_types = ['inventory']
            import_type = parsed_args.import_type
            if not import_type or import_type not in legal_types:
                raise CommandError(u._(
                    'Import type must be {type}.').format(type=legal_types))

            file_path = None
            if parsed_args.file_path:
                file_path = parsed_args.file_path.strip()
            CLIENT.config_import_inventory(file_path)
        except Exception:
            raise Exception(traceback.format_exc())
