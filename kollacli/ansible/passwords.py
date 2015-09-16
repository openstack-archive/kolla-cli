# Copyright(c) 2015, Oracle and/or its affiliates.  All Rights Reserved.
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

from kollacli.exceptions import CommandError
from kollacli import utils

PWDS_FILENAME = 'passwords.yml'
PWD_EDITOR_FILENAME = 'passwd_editor.py'


def set_password(pwd_key, pwd_value):
    """set a password value

    If the password name exists, it will be changed.
    If it doesn't exist, a new password will be added.
    """
    editor_path = os.path.join(utils.get_kollacli_home(),
                               'tools',
                               PWD_EDITOR_FILENAME)

    pwd_file_path = os.path.join(utils.get_kolla_etc(),
                                 PWDS_FILENAME)

    cmd = 'sudo %s -p %s -k %s -v %s' % (editor_path, pwd_file_path,
                                         pwd_key, pwd_value)

    err, output = utils.run_cmd(cmd, print_output=False)
    if err:
        raise CommandError(output)


def clear_password(pwd_key):
    """clear a password

    if the password exists, it will be removed from the passwords file
    """
    editor_path = os.path.join(utils.get_kollacli_home(),
                               'tools',
                               PWD_EDITOR_FILENAME)

    pwd_file_path = os.path.join(utils.get_kolla_etc(),
                                 PWDS_FILENAME)

    cmd = 'sudo %s -p %s -k %s -c' % (editor_path, pwd_file_path,
                                      pwd_key)

    err, output = utils.run_cmd(cmd, print_output=False)
    if err:
        raise CommandError(output)


def get_password_names():
    """return a list of password names"""
    editor_path = os.path.join(utils.get_kollacli_home(),
                               'tools',
                               PWD_EDITOR_FILENAME)

    pwd_file_path = os.path.join(utils.get_kolla_etc(),
                                 PWDS_FILENAME)

    cmd = 'sudo %s -p %s -l' % (editor_path, pwd_file_path)

    err, output = utils.run_cmd(cmd, print_output=False)
    if err:
        raise CommandError(output)

    pwd_names = []
    if output and ',' in output[0]:
        pwd_names = output[0].split(',')
    return pwd_names
