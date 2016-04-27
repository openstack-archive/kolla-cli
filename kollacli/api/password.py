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
from blaze.api.password import PasswordApi as BlazePasswordApi
from kollacli.common.utils import reraise


class PasswordApi(object):

    def password_set(self, name, value):
        """Set password

        :param name: name of the password
        :type name: string
        :param value: value of the password
        :type value: string
        """
        try:
            BlazePasswordApi().password_set(name, value)
        except Exception as e:
            reraise(e)

    def password_clear(self, name):
        """Clear password

        :param name: name of the password
        :type name: string
        """
        try:
            BlazePasswordApi().password_clear(name)
        except Exception as e:
            reraise(e)

    def password_get_names(self):
        """Get password names

        :return: password names
        :rtype: list of strings
        """
        try:
            return BlazePasswordApi().password_get_names()
        except Exception as e:
            reraise(e)
