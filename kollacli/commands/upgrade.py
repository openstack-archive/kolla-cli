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

from cliff.command import Command

import kollacli.i18n as u

from kollacli.api.client import ClientApi
from kollacli.commands.exceptions import CommandError


CLIENT = ClientApi()

LOG = logging.getLogger(__name__)


class Upgrade(Command):
    """Upgrade."""
    def get_parser(self, prog_name):
        parser = super(Upgrade, self).get_parser(prog_name)
        parser.add_argument('--services', nargs='?',
                            metavar='<service_list>',
                            help=u._('Upgrade service list'))
        return parser

    def take_action(self, parsed_args):
        services = None
        try:
            if parsed_args.services:
                service_list = parsed_args.services.strip()
                services = service_list.split(',')
            verbose_level = self.app.options.verbose_level
            job = CLIENT.upgrade(verbose_level, services)
            status = job.wait()
            if verbose_level > 2:
                LOG.info('\n\n' + 80 * '=')
                LOG.info(u._('DEBUG command output:\n{out}')
                         .format(out=job.get_console_output()))
            if status == 0:
                LOG.info(u._('Success'))
            else:
                raise CommandError(u._('Job failed:\n{msg}')
                                   .format(msg=job.get_error_message()))

        except Exception:
            raise Exception(traceback.format_exc())
