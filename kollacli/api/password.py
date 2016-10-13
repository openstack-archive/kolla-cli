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
import kollacli.i18n as u

from kollacli.common.passwords import clear_password
from kollacli.common.passwords import get_password_names
from kollacli.common.passwords import init_passwords
from kollacli.common.passwords import set_password
from kollacli.common.passwords import set_password_sshkey
from kollacli.common.utils import check_arg


class PasswordApi(object):

    def password_set(self, name, value):
        # type: (str, str) -> None
        """Set password

        :param name: name of the password
        :type name: string
        :param value: value of the password
        :type value: string
        """
        check_arg(name, u._('Password name'), str)
        check_arg(value, u._('Password value'), str, display_param=False,
                  empty_ok=True, none_ok=True)
        set_password(name, value)

    def password_set_sshkey(self, name, private_key, public_key):
        # type: (str, str, str) -> None
        """Set password to an ssh key

        :param name: name of the password
        :type name: string
        :param private_key: ssh private key
        :type value: string
        :param public_key: ssh public key
        :type value: string
        """
        check_arg(name, u._('Password name'), str)
        check_arg(private_key, u._('Private key'), str, display_param=False)
        check_arg(public_key, u._('Public key'), str, display_param=False)
        set_password_sshkey(name, private_key, public_key)

    def password_clear(self, name):
        # type: (str) -> None
        """Clear password

        :param name: name of the password
        :type name: string
        """
        check_arg(name, u._('Password name'), str)
        clear_password(name)

    def password_get_names(self):
        # type: () -> List[str]
        """Get password names

        :return: password names
        :rtype: list of strings
        """
        return get_password_names()

    def password_init(self):
        # type: () -> None
        """Init empty passwords

        Init empty passwords and ssh keys in /etc/kolla/passwords.yml
        to auto-generated values
        """
        return init_passwords()
