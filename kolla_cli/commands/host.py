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

import argparse
import getpass
import logging
import os
import traceback
import yaml

from cliff.command import Command
from cliff.lister import Lister
from six.moves import input

from kolla_cli.api.client import ClientApi
from kolla_cli.api.exceptions import ClientException
from kolla_cli.commands.exceptions import CommandError
from kolla_cli.common.utils import convert_lists_to_string
from kolla_cli.common.utils import get_setup_user
from kolla_cli.common.utils import handers_action_result
import kolla_cli.i18n as u

LOG = logging.getLogger(__name__)
CLIENT = ClientApi()


class HostAdd(Command):
    """Add host to openstack-kolla."""

    def get_parser(self, prog_name):
        parser = super(HostAdd, self).get_parser(prog_name)
        parser.add_argument('hostname', metavar='<hostname>',
                            help=u._('Host name or ip address'))
        return parser

    def take_action(self, parsed_args):
        try:
            hostname = parsed_args.hostname.strip()
            CLIENT.host_add([hostname])

        except ClientException as e:
            raise CommandError(str(e))
        except Exception:
            raise Exception(traceback.format_exc())


class HostDestroy(Command):
    """Destroy all kolla containers on host(s).

    Stops and removes all kolla related docker containers on either the
    specified host or all hosts if the hostname all is used.
    """

    def get_parser(self, prog_name):
        parser = super(HostDestroy, self).get_parser(prog_name)
        parser.add_argument('hostname', metavar='<hostname | all>',
                            help=u._('Host name or ip address or "all"'))
        parser.add_argument('--stop', action='store_true',
                            help=u._('Stop rather than kill'))
        parser.add_argument('--includedata', action='store_true',
                            help=u._('Destroy data containers'))
        parser.add_argument('--removeimages', action='store_true',
                            help=u._('Remove docker images'))
        return parser

    def take_action(self, parsed_args):
        try:
            hostname = parsed_args.hostname.strip()

            hostnames = [hostname]
            if hostname == 'all':
                hostnames = _get_all_hostnames()
                # if there are no hosts, don't bother doing anything
                if not hostnames:
                    return

            destroy_type = 'kill'
            if parsed_args.stop:
                destroy_type = 'stop'
            include_data = False
            if parsed_args.includedata:
                include_data = True
            remove_images = False
            if parsed_args.removeimages:
                remove_images = True

            if include_data and not self._is_ok_to_delete_data():
                LOG.info('Aborting destroy')
                return

            verbose_level = self.app.options.verbose_level

            job = CLIENT.host_destroy(hostnames, destroy_type,
                                      verbose_level, include_data,
                                      remove_images)
            status = job.wait()
            handers_action_result(job, status, verbose_level)
        except ClientException as e:
            raise CommandError(str(e))
        except Exception:
            raise Exception(traceback.format_exc())

    def _is_ok_to_delete_data(self):
        question = ('This will delete all containers and data'
                    ', are you sure? (y/n)')
        answer = input(question)
        while answer != 'y' and answer != 'n':
            answer = input(question)
        return True if answer == 'y' else False


class HostRemove(Command):
    """Remove host from openstack-kolla."""

    def get_parser(self, prog_name):
        parser = super(HostRemove, self).get_parser(prog_name)
        parser.add_argument('hostname', metavar='<hostname | all>',
                            help=u._('Host name or "all"'))
        return parser

    def take_action(self, parsed_args):
        try:
            hostname = parsed_args.hostname.strip()
            hostnames = [hostname]
            if hostname == 'all':
                hostnames = _get_all_hostnames()
            if len(hostnames) > 0:
                CLIENT.host_remove(hostnames)

        except ClientException as e:
            raise CommandError(str(e))
        except Exception:
            raise Exception(traceback.format_exc())


class HostList(Lister):
    """List hosts and their groups.

    If a hostname is provided, only list information about that host.
    """

    def get_parser(self, prog_name):
        parser = super(HostList, self).get_parser(prog_name)
        parser.add_argument('hostname', nargs='?', metavar='[hostname]',
                            help=u._('Host name'))
        return parser

    def take_action(self, parsed_args):
        try:
            hostname = None
            if parsed_args.hostname:
                hostname = parsed_args.hostname.strip()

            hosts = []
            if hostname:
                hosts = CLIENT.host_get([hostname])
            else:
                hosts = CLIENT.host_get_all()

            data = []
            if hosts:
                for host in hosts:
                    data.append((host.name, host.get_groups()))
            else:
                data.append(('', ''))

            data = convert_lists_to_string(data, parsed_args)
            return ((u._('Host'), u._('Groups')), sorted(data))

        except ClientException as e:
            raise CommandError(str(e))
        except Exception:
            raise Exception(traceback.format_exc())


class HostCheck(Command):
    """Check an ssh check of host(s)."""

    def get_parser(self, prog_name):
        parser = super(HostCheck, self).get_parser(prog_name)
        parser.add_argument('hostname', metavar='<hostname | all>',
                            help=u._('Host name or "all"'))
        return parser

    def take_action(self, parsed_args):
        try:
            hostname = parsed_args.hostname.strip()
            if hostname == 'all':
                hostnames = _get_all_hostnames()
            else:
                hostnames = [hostname]

            # just do an ssh check
            summary = CLIENT.host_ssh_check(hostnames)
            all_ok = True
            for hostname, info in summary.items():
                status = u._('success')
                msg = ''
                if not info['success']:
                    status = u._('failed-')
                    msg = info['msg']
                    all_ok = False
                LOG.info(u._('Host {host}: {sts} {msg}')
                         .format(host=hostname, sts=status, msg=msg))

            if not all_ok:
                raise CommandError(u._('Host check failed.'))
        except ClientException as e:
            raise CommandError(str(e))
        except Exception:
            raise Exception(traceback.format_exc())


class HostSetup(Command):
    """Setup kolla-cli on host."""

    def get_parser(self, prog_name):
        parser = super(HostSetup, self).get_parser(prog_name)
        parser.add_argument('hostname', nargs='?',
                            metavar='<hostname>', help=u._('Host name'))
        parser.add_argument('--insecure', nargs='?', help=argparse.SUPPRESS)
        parser.add_argument('--file', '-f', nargs='?',
                            metavar='<hosts_info_file>',
                            help=u._('Absolute path to hosts info file '))
        return parser

    def take_action(self, parsed_args):
        try:
            if not parsed_args.hostname and not parsed_args.file:
                raise CommandError(
                    u._('Host name or hosts info file path is required.'))
            if parsed_args.hostname and parsed_args.file:
                raise CommandError(
                    u._('Host name and hosts info file path '
                        'cannot both be present.'))

            if parsed_args.file:
                # multi-host setup via xml file
                # The xml file's content is like a dict of format:
                # hostname1:
                #     uname: user1
                #     password: <password1>
                # hostname2:
                #     uname: user2
                #     password: <password2>
                hosts_data = self._get_yml_data(parsed_args.file.strip())
                CLIENT.host_setup(hosts_data)
            else:
                # single host setup
                hostname = parsed_args.hostname.strip()
                summary = CLIENT.host_ssh_check([hostname])
                if summary[hostname]['success']:
                    LOG.info(
                        u._LI('Skipping setup of host ({host}) as '
                              'ssh check is ok.').format(host=hostname))
                    return 0

                if parsed_args.insecure:
                    password = parsed_args.insecure.strip()
                else:
                    password = getpass.getpass(
                        u._('{name} password for {host}: ')
                        .format(name=get_setup_user(), host=hostname))
                CLIENT.host_setup({hostname: {'password': password}})

        except ClientException as e:
            raise CommandError(str(e))
        except Exception:
            raise Exception(traceback.format_exc())

    def _get_yml_data(self, yml_path):
        if not os.path.isfile(yml_path):
            raise CommandError(
                u._('No file exists at {path}. An absolute file path is '
                    'required.').format(path=yml_path))

        with open(yml_path, 'r') as hosts_file:
            file_data = hosts_file.read()

        hosts_info = yaml.safe_load(file_data)
        if not hosts_info:
            raise CommandError(u._('{path} is empty.').format(path=yml_path))
        return hosts_info


def _get_all_hostnames():
    hostnames = []
    hosts = CLIENT.host_get_all()
    for host in hosts:
        hostnames.append(host.name)
    return hostnames
