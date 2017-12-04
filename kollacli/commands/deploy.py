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
import time
import traceback

import kollacli.i18n as u

from kollacli.api.client import ClientApi
from kollacli.commands.exceptions import CommandError

from cliff.command import Command

LOG = logging.getLogger(__name__)
CLIENT = ClientApi()


class Deploy(Command):
    """Deploy containers to hosts."""
    def get_parser(self, prog_name):
        parser = super(Deploy, self).get_parser(prog_name)
        parser.add_argument('--hosts', nargs='?',
                            metavar='<host_list>',
                            help=u._('Deployment host list'))
        parser.add_argument('--serial', action='store_true',
                            help=u._('Deploy serially'))
        parser.add_argument('--timeout', nargs=1,
                            metavar='<timeout>',
                            help=u._('timeout (in minutes)'))
        return parser

    def take_action(self, parsed_args):
        hosts = None
        serial_flag = False
        verbose_level = self.app.options.verbose_level
        timeout_target = 0
        try:
            if parsed_args.hosts:
                host_list = parsed_args.hosts.strip()
                hosts = host_list.split(',')
            if parsed_args.serial:
                serial_flag = True
            if parsed_args.timeout:
                try:
                    timeout = float(parsed_args.timeout[0])
                except Exception:
                    raise CommandError(u._('Timeout value is not a number.'))
                timeout_target = time.time() + (60 * timeout)

            # if we are doing a targeted host deploy make sure we are doing it
            # to only compute nodes
            if hosts:
                invalid_host_list = []
                compute_group = CLIENT.group_get(['compute'])[0]
                compute_hosts = compute_group.get_hosts()
                for host in hosts:
                    if host not in compute_hosts:
                        invalid_host_list.append(host)
                if len(invalid_host_list) > 0:
                    raise CommandError(
                        u._('Invalid hosts for host targeted deploy. '
                            'Hosts must be in the compute group only.'
                            'Invalid hosts: {hosts}')
                        .format(hosts=invalid_host_list))

            job = CLIENT.deploy(hosts, serial_flag,
                                verbose_level)

            # wait for job to complete
            status = None
            while status is None:
                if timeout_target and time.time() > timeout_target:
                    job.kill()
                    raise CommandError(u._('Job timed out and was killed.'))
                time.sleep(1)
                status = job.get_status()

            # job is done
            if verbose_level > 2:
                LOG.info('\n\n' + 80 * '=')
                LOG.info(u._('DEBUG command output:\n{out}')
                         .format(out=job.get_console_output()))
            if status == 0:
                if verbose_level > 1:
                    # log any ansible warnings
                    msg = job.get_error_message()
                    if msg:
                        LOG.warn(msg)
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
