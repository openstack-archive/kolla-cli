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
import os
import traceback

from cliff.command import Command
from cliff.lister import Lister

from kolla_cli.api.client import ClientApi
from kolla_cli.commands.exceptions import CommandError
import kolla_cli.i18n as u

CLIENT = ClientApi()


class PasswordSet(Command):
    "Password Set"

    def get_parser(self, prog_name):
        parser = super(PasswordSet, self).get_parser(prog_name)
        parser.add_argument('passwordname', metavar='<passwordname>',
                            help=u._('Password name'))
        parser.add_argument('--insecure', nargs='?', default=False,
                            help=argparse.SUPPRESS)
        return parser

    def take_action(self, parsed_args):
        try:
            password_name = parsed_args.passwordname.strip()
            if parsed_args.insecure is not False:
                # --insecure flag is present
                password = ''  # nosec
                if parsed_args.insecure:
                    password = parsed_args.insecure.strip()
            else:
                password = getpass.getpass(u._('Password: ')).strip()
                passtwo = getpass.getpass(u._('Retype Password: ')).strip()

                if password != passtwo:
                    raise CommandError(u._('Passwords do not match'))

            CLIENT.password_set(password_name, password)

        except Exception:
            raise Exception(traceback.format_exc())


class PasswordSetKey(Command):
    "Password Set SSH Key"

    def get_parser(self, prog_name):
        parser = super(PasswordSetKey, self).get_parser(prog_name)
        parser.add_argument('passwordname', metavar='<passwordname>',
                            help=u._('Password name'))
        parser.add_argument('privatekeypath', metavar='<privatekeypath>',
                            help=u._('Path to private key file'))
        parser.add_argument('publickeypath', metavar='<publickeypath>',
                            help=u._('Path to public key file'))
        return parser

    def take_action(self, parsed_args):
        try:
            password_name = parsed_args.passwordname.strip()
            private_keypath = parsed_args.privatekeypath.strip()
            private_keypath = os.path.abspath(private_keypath)
            public_keypath = parsed_args.publickeypath.strip()
            public_keypath = os.path.abspath(public_keypath)

            if not os.path.isfile(private_keypath):
                raise(CommandError(u._('Private key file not found: {path}')
                                   .format(path=private_keypath)))
            if not os.path.isfile(public_keypath):
                raise(CommandError(u._('Public key file not found: {path}')
                                   .format(path=public_keypath)))

            with open(private_keypath, 'r') as f:
                private_key = f.read()
            with open(public_keypath, 'r') as f:
                public_key = f.read()
            CLIENT.password_set_sshkey(password_name, private_key.strip(),
                                       public_key.strip())

        except Exception:
            raise Exception(traceback.format_exc())


class PasswordClear(Command):
    "Password Clear"

    def get_parser(self, prog_name):
        parser = super(PasswordClear, self).get_parser(prog_name)
        parser.add_argument('passwordname', metavar='<passwordname>',
                            help=u._('Password name'))
        return parser

    def take_action(self, parsed_args):
        try:
            password_name = parsed_args.passwordname.strip()
            CLIENT.password_clear(password_name)
        except Exception:
            raise Exception(traceback.format_exc())


class PasswordList(Lister):
    """List all password names."""

    def take_action(self, parsed_args):
        try:
            password_names = CLIENT.password_get_names()
            password_names = sorted(password_names)

            data = []
            for password_name in password_names:
                data.append((password_name, '-'))

            return ((u._('Password Name'),  u._('Password')), data)
        except Exception:
            raise Exception(traceback.format_exc())


class PasswordInit(Command):
    """Init all empty passwords and ssh keys."""

    def take_action(self, parsed_args):
        try:
            CLIENT.password_init()
        except Exception:
            raise Exception(traceback.format_exc())
