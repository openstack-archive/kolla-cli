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

import kollacli.i18n as u

from kollacli.common import utils
from kollacli.exceptions import CommandError

PWDS_FILENAME = 'passwords.yml'
PWD_EDITOR_FILENAME = 'passwd_editor.py'


def set_password(pwd_key, pwd_value):
    """set a password value

    If the password name exists, it will be changed.
    If it doesn't exist, a new password will be added.
    """
    cmd = '%s -k %s -v %s' % (_get_cmd_prefix(), pwd_key, pwd_value)
    err_msg, output = utils.run_cmd(cmd, print_output=False)
    if err_msg:
        raise CommandError(
            u._('Password set failed. {error} {message}')
            .format(error=err_msg, message=output))


def clear_password(pwd_key):
    """clear a password

    if the password exists, it will be removed from the passwords file
    """
    cmd = '%s -k %s -c' % (_get_cmd_prefix(), pwd_key)
    err_msg, output = utils.run_cmd(cmd, print_output=False)
    if err_msg:
        raise CommandError('%s %s' % (err_msg, output))


def get_password_names():
    """return a list of password names"""
    cmd = '%s -l' % (_get_cmd_prefix())
    err_msg, output = utils.run_cmd(cmd, print_output=False)
    if err_msg:
        raise CommandError('%s %s' % (err_msg, output))

    pwd_names = []
    if output and ',' in output:
        pwd_names = output.strip().split(',')
    return pwd_names


def _get_cmd_prefix():
    editor_path = os.path.join(utils.get_kollacli_home(),
                               'tools',
                               PWD_EDITOR_FILENAME)
    pwd_file_path = os.path.join(utils.get_kolla_etc(),
                                 PWDS_FILENAME)
    user = utils.get_admin_user()
    prefix = '/usr/bin/sudo -u %s %s -p %s ' % (user,
                                                editor_path, pwd_file_path)
    return prefix
