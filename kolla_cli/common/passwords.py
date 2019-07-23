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

import os

from kolla_cli.api.exceptions import FailedOperation
from kolla_cli.common import utils
import kolla_cli.i18n as u

PWDS_FILENAME = 'passwords.yml'


def set_password(pwd_key, pwd_value):
    """set a password value

    If the password name exists, it will be changed.
    If it doesn't exist, a new password will be added.
    """
    value_switch = '-v'
    if not pwd_value:
        pwd_value = ''
        value_switch = ''
    cmd = '%s -k \'%s\' %s \'%s\'' % (_get_cmd_prefix(), pwd_key, value_switch,
                                      pwd_value)
    err_msg, output = utils.run_cmd(cmd, print_output=False)
    if err_msg:
        raise FailedOperation(
            u._('Password set failed. {error} {message}')
            .format(error=err_msg, message=output))


def set_password_sshkey(pwd_key, private_key, public_key):
    cmd = '%s -k \'%s\' -r \'%s\' -u \'%s\'' % (_get_cmd_prefix(), pwd_key,
                                                private_key, public_key)
    err_msg, output = utils.run_cmd(cmd, print_output=False)
    if err_msg:
        raise FailedOperation(
            u._('Password ssh key set failed. {error} {message}')
            .format(error=err_msg, message=output))


def clear_password(pwd_key):
    """clear a password

    if the password exists, it will be removed from the passwords file
    """
    cmd = '%s -k \'%s\' -c' % (_get_cmd_prefix(), pwd_key)
    err_msg, output = utils.run_cmd(cmd, print_output=False)
    if err_msg:
        raise FailedOperation('%s %s' % (err_msg, output))


def get_password_names():
    """return a list of password names"""
    cmd = '%s -l' % (_get_cmd_prefix())
    err_msg, output = utils.run_cmd(cmd, print_output=False)
    if err_msg:
        raise FailedOperation('%s %s' % (err_msg, output))

    pwd_names = []
    if output and ',' in output:
        pwd_names = output.strip().split(',')
    return pwd_names


def get_empty_password_values():
    cmd = '%s -e' % (_get_cmd_prefix())
    err_msg, output = utils.run_cmd(cmd, print_output=False)
    # output of this command is a comma separated string of password keys
    # that have empty values.
    if err_msg:
        raise FailedOperation('%s %s' % (err_msg, output))

    empty_keys = []
    if output:
        # password keys exist that have no values
        empty_keys = output.strip().split(',')
    return empty_keys


def init_passwords():
    # init empty passwords & ssh keys to auto-gen'd values
    cmd = '%s -i' % (_get_cmd_prefix())
    err_msg, output = utils.run_cmd(cmd, print_output=False)
    if err_msg:
        raise FailedOperation('%s %s' % (err_msg, output))


def _get_cmd_prefix():
    actions_path = utils.get_kolla_actions_path()
    pwd_file_path = os.path.join(utils.get_kolla_etc(),
                                 PWDS_FILENAME)
    prefix = ('%s password -p %s '
              % (actions_path, pwd_file_path))
    return prefix
