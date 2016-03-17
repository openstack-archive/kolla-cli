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

import kollacli.i18n as u

from kollacli.api.client import ClientApi
from kollacli.common.utils import convert_to_unicode
from kollacli.exceptions import CommandError

from cliff.command import Command

LOG = logging.getLogger(__name__)
CLIENT = ClientApi()


class Deploy(Command):
    """Deploy."""
    def get_parser(self, prog_name):
        parser = super(Deploy, self).get_parser(prog_name)
        parser.add_argument('--hosts', nargs='?',
                            metavar='<host_list>',
                            help=u._('Deployment host list'))
        parser.add_argument('--groups', nargs='?',
                            metavar='<group_list>',
                            help=u._('Deployment group list'))
        parser.add_argument('--services', nargs='?',
                            metavar='<service_list>',
                            help=u._('Deployment service list'))
        parser.add_argument('--serial', action='store_true',
                            help=u._('Deploy serially'))
        return parser

    def take_action(self, parsed_args):
        hosts = None
        groups = None
        services = None
        serial_flag = False
        verbose_level = self.app.options.verbose_level
        try:
            if parsed_args.hosts:
                host_list = parsed_args.hosts.strip()
                hosts = convert_to_unicode(host_list).split(',')
            if parsed_args.groups:
                group_list = parsed_args.groups.strip()
                groups = convert_to_unicode(group_list).split(',')
            if parsed_args.services:
                service_list = parsed_args.services.strip()
                services = convert_to_unicode(service_list).split(',')
            if parsed_args.serial:
                serial_flag = True

            job = CLIENT.async_deploy(hosts, groups, services, serial_flag,
                                      verbose_level)
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


class Setdeploy(Command):
    """Set deploy mode.

    Set deploy mode to either local or remote. Local indicates
    that the openstack deployment will be to the local host.
    Remote means that the deployment is on remote hosts.
    """
    def get_parser(self, prog_name):
        parser = super(Setdeploy, self).get_parser(prog_name)
        parser.add_argument('mode', metavar='<mode>',
                            help=u._('mode=<local, remote>'))
        return parser

    def take_action(self, parsed_args):
        try:
            mode = parsed_args.mode.strip()
            remote_flag = False
            if mode == 'remote':
                remote_flag = True
            elif mode != 'local':
                raise CommandError(
                    u._('Invalid deploy mode. Mode must be '
                        'either "local" or "remote".'))
            CLIENT.deploy_set_mode(remote_flag)
        except CommandError as e:
            raise e
        except Exception:
            raise Exception(traceback.format_exc())
