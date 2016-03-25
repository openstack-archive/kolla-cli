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
from kollacli.common.passwords import set_password
from kollacli.common.utils import check_arg


class PasswordApi(object):

    def password_set(self, name, value):
        """Set password

        :param name: name of the password
        :type name: string
        :param value: value of the password
        :type value: string
        """
        check_arg(name, u._('Password name'), str)
        set_password(name, value)

    def password_clear(self, name):
        """Clear password

        :param name: name of the password
        :type name: string
        """
        check_arg(name, u._('Password name'), str)
        clear_password(name)

    def password_get_names(self):
        """Get password names

        :return: password names
        :rtype: list of strings
        """
        return get_password_names()
