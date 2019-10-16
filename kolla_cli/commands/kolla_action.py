# Copyright(c) 2017, Oracle and/or its affiliates.  All Rights Reserved.
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

from cliff.command import Command

from kolla_cli.api.client import ClientApi
from kolla_cli.commands.exceptions import CommandError
from kolla_cli.common.utils import handers_action_result
import kolla_cli.i18n as u

CLIENT = ClientApi()
LOG = logging.getLogger(__name__)


class Deploy(Command):
    """Deploy and start all kolla containers."""
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
        parser.add_argument('--services', nargs='?',
                            metavar='<service_list>',
                            help=u._('Deploy service list'))
        return parser

    def take_action(self, parsed_args):
        hosts = None
        serial_flag = False
        verbose_level = self.app.options.verbose_level
        timeout_target = 0
        services = None
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
            if parsed_args.services:
                service_list = parsed_args.services.strip()
                services = service_list.split(',')

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

            job = CLIENT.deploy(hosts, serial_flag, verbose_level, services)

            # wait for job to complete
            status = None
            while status is None:
                if timeout_target and time.time() > timeout_target:
                    job.kill()
                    raise CommandError(u._('Job timed out and was killed.'))
                time.sleep(1)
                status = job.get_status()

            # job is done
            handers_action_result(job, status, verbose_level)
        except Exception:
            raise Exception(traceback.format_exc())


class Prechecks(Command):
    """Do pre-deployment checks for hosts."""
    def get_parser(self, prog_name):
        parser = super(Prechecks, self).get_parser(prog_name)
        parser.add_argument('--hosts', nargs='?',
                            metavar='<host_list>',
                            help=u._('Precheck host list'))
        parser.add_argument('--services', nargs='?',
                            metavar='<service_list>',
                            help=u._('Precheck service list'))
        return parser

    def take_action(self, parsed_args):
        hosts = []
        services = []
        try:
            verbose_level = self.app.options.verbose_level

            if parsed_args.hosts:
                host_list = parsed_args.hosts.strip()
                hosts = host_list.split(',')
            if parsed_args.services:
                service_list = parsed_args.services.strip()
                services = service_list.split(',')
            job = CLIENT.prechecks(verbose_level, hosts, services)
            status = job.wait()
            handers_action_result(job, status, verbose_level)
        except Exception:
            raise Exception(traceback.format_exc())


class Pull(Command):
    """Pull all images for containers (only pulls, no running container)."""
    def get_parser(self, prog_name):
        parser = super(Pull, self).get_parser(prog_name)
        parser.add_argument('--hosts', nargs='?',
                            metavar='<host_list>',
                            help=u._('Pull host list'))
        parser.add_argument('--services', nargs='?',
                            metavar='<service_list>',
                            help=u._('Pull service list'))
        return parser

    def take_action(self, parsed_args):
        hosts = []
        services = []
        try:
            verbose_level = self.app.options.verbose_level
            if parsed_args.hosts:
                host_list = parsed_args.hosts.strip()
                hosts = host_list.split(',')
            if parsed_args.services:
                service_list = parsed_args.services.strip()
                services = service_list.split(',')
            job = CLIENT.pull(verbose_level, hosts, services)
            status = job.wait()
            handers_action_result(job, status, verbose_level)
        except Exception:
            raise Exception(traceback.format_exc())


class Reconfigure(Command):
    """Reconfigure OpenStack service."""
    def get_parser(self, prog_name):
        parser = super(Reconfigure, self).get_parser(prog_name)
        parser.add_argument('--hosts', nargs='?',
                            metavar='<host_list>',
                            help=u._('Reconfigure host list'))
        parser.add_argument('--services', nargs='?',
                            metavar='<service_list>',
                            help=u._('Reconfigure service list'))
        return parser

    def take_action(self, parsed_args):
        hosts = []
        services = []
        try:
            verbose_level = self.app.options.verbose_level
            if parsed_args.hosts:
                host_list = parsed_args.hosts.strip()
                hosts = host_list.split(',')
            if parsed_args.services:
                service_list = parsed_args.services.strip()
                services = service_list.split(',')
            job = CLIENT.reconfigure(verbose_level, hosts, services)
            status = job.wait()
            handers_action_result(job, status, verbose_level)
        except Exception:
            raise Exception(traceback.format_exc())


class Stop(Command):
    """Stop all kolla containers on host(s).

    Stops all kolla related docker containers on either the
    specified host or all hosts if the hostname all is used.
    """
    def get_parser(self, prog_name):
        parser = super(Stop, self).get_parser(prog_name)
        parser.add_argument('--hosts', nargs='?',
                            metavar='<host_list>',
                            help=u._('Stop host list'))
        parser.add_argument('--services', nargs='?',
                            metavar='<service_list>',
                            help=u._('Stop service list'))
        return parser

    def take_action(self, parsed_args):
        try:
            hosts = []
            services = []
            verbose_level = self.app.options.verbose_level
            if parsed_args.hosts:
                host_list = parsed_args.hosts.strip()
                hosts = host_list.split(',')
            if parsed_args.services:
                service_list = parsed_args.services.strip()
                services = service_list.split(',')
            job = CLIENT.stop(verbose_level, hosts, services)
            status = job.wait()
            handers_action_result(job, status, verbose_level)
        except Exception:
            raise Exception(traceback.format_exc())


class Upgrade(Command):
    """Upgrades existing OpenStack Environment."""
    def get_parser(self, prog_name):
        parser = super(Upgrade, self).get_parser(prog_name)
        parser.add_argument('--hosts', nargs='?',
                            metavar='<host_list>',
                            help=u._('Upgrade host list'))
        parser.add_argument('--services', nargs='?',
                            metavar='<service_list>',
                            help=u._('Upgrade service list'))
        return parser

    def take_action(self, parsed_args):
        hosts = []
        services = []
        try:
            if parsed_args.hosts:
                host_list = parsed_args.hosts.strip()
                hosts = host_list.split(',')
            if parsed_args.services:
                service_list = parsed_args.services.strip()
                services = service_list.split(',')
            verbose_level = self.app.options.verbose_level
            job = CLIENT.upgrade(verbose_level, hosts, services)
            status = job.wait()
            handers_action_result(job, status, verbose_level)
        except Exception:
            raise Exception(traceback.format_exc())


class Check(Command):
    """Do post-deployment smoke tests."""
    def get_parser(self, prog_name):
        parser = super(Check, self).get_parser(prog_name)
        parser.add_argument('--hosts', nargs='?',
                            metavar='<host_list>',
                            help=u._('Check host list'))
        parser.add_argument('--services', nargs='?',
                            metavar='<service_list>',
                            help=u._('Check service list'))
        return parser

    def take_action(self, parsed_args):
        hosts = []
        services = None
        try:
            if parsed_args.hosts:
                host_list = parsed_args.hosts.strip()
                hosts = host_list.split(',')
            if parsed_args.services:
                service_list = parsed_args.services.strip()
                services = service_list.split(',')
            verbose_level = self.app.options.verbose_level
            job = CLIENT.check(verbose_level, hosts, services)
            status = job.wait()
            handers_action_result(job, status, verbose_level)
        except Exception:
            raise Exception(traceback.format_exc())


class Genconfig(Command):
    """Generate configuration files for enabled OpenStack services."""
    def get_parser(self, prog_name):
        parser = super(Genconfig, self).get_parser(prog_name)
        parser.add_argument('--hosts', nargs='?',
                            metavar='<host_list>',
                            help=u._('genarate configs host list'))
        parser.add_argument('--services', nargs='?',
                            metavar='<service_list>',
                            help=u._('genarate configs service list'))
        return parser

    def take_action(self, parsed_args):
        hosts = []
        services = []
        try:
            verbose_level = self.app.options.verbose_level
            if parsed_args.hosts:
                host_list = parsed_args.hosts.strip()
                hosts = host_list.split(',')
            if parsed_args.services:
                service_list = parsed_args.services.strip()
                services = service_list.split(',')
            job = CLIENT.genconfig(verbose_level, hosts, services)
            status = job.wait()
            handers_action_result(job, status, verbose_level)
        except Exception:
            raise Exception(traceback.format_exc())


class PostDeploy(Command):
    """Do post deploy on deploy node."""

    def take_action(self, parsed_args):
        verbose_level = self.app.options.verbose_level
        try:
            job = CLIENT.postdeploy(verbose_level)
            status = job.wait()
            handers_action_result(job, status, verbose_level)
        except Exception:
            raise Exception(traceback.format_exc())


class CertificateInit(Command):
    """Generates self-signed certificate"""

    def take_action(self, parsed_args):
        verbose_level = self.app.options.verbose_level
        try:
            job = CLIENT.certificate_init(verbose_level)

            # wait for job to complete
            status = job.wait()
            handers_action_result(job, status, verbose_level)
        except Exception:
            raise Exception(traceback.format_exc())
