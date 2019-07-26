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

from kolla_cli.api.client import ClientApi
from kolla_cli.commands.exceptions import CommandError
import kolla_cli.i18n as u

LOG = logging.getLogger(__name__)
CLIENT = ClientApi()


class Setdeploy(Command):
    """Set deploy mode to either local or remote.

    Local indicates that the openstack deployment will be
    to the local host. Remote means that the deployment is
    on remote hosts.
    """
    def get_parser(self, prog_name):
        parser = super(Setdeploy, self).get_parser(prog_name)
        parser.add_argument('mode', metavar='<mode>',
                            help=u._('mode=<local, remote>'))
        return parser

    def take_action(self, parsed_args):
        try:
            mode = parsed_args.mode.strip()
            remote_flag = True
            if mode == 'local':
                remote_flag = False
                LOG.info(u._('Please note that local mode is not supported '
                             'and should never be used in production '
                             'environments.'))
            elif mode != 'remote':
                raise CommandError(
                    u._('Invalid deploy mode. Mode must be '
                        'either "local" or "remote".'))
            CLIENT.set_deploy_mode(remote_flag)
        except CommandError as e:
            raise e
        except Exception:
            raise Exception(traceback.format_exc())


class Getdeploy(Command):
    """get deploy mode from either local or remote.

    Local indicates that the openstack deployment will be
    to the local host. Remote means that the deployment is
    on remote hosts.
    """

    def take_action(self, parsed_args):
        try:
            mode = CLIENT.get_deploy_mode()
            return mode
        except CommandError as e:
            raise e
        except Exception:
            raise Exception(traceback.format_exc())
