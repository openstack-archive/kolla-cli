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

"""Exception definitions."""
import kolla_cli.i18n as u


class ClientException(Exception):
    """KollaClient Base Class Exception"""
    def __init__(self, message, *args):
        if not message:
            message = u._('An unknown exception occurred.')
        super(ClientException, self).__init__(message, *args)


class NotInInventory(ClientException):
    """Not in inventory exception"""
    def __init__(self, obj_type, obj_names, *args):
        if isinstance(obj_names, list):
            # list of names
            invalid_objs = ''
            comma = ''
            for obj_name in obj_names:
                invalid_objs = ''.join([invalid_objs, comma, obj_name])
                comma = ','
        else:
            # single object name
            invalid_objs = obj_names
        message = (u._('{type} ({objs}) does not exist.')
                   .format(type=obj_type, objs=invalid_objs))
        super(NotInInventory, self).__init__(message, *args)


class HostError(ClientException):
    pass


class HostsSshCheckError(ClientException):
    """Host failed its ssh check"""
    def __init__(self, hostnames, *args):
        failed_hosts = ''
        comma = ''
        for hostname in hostnames:
            failed_hosts = ''.join([failed_hosts, comma, hostname])
            comma = ','
        message = (u._('Host(s) ssh check failed: {hosts}')
                   .format(hosts=failed_hosts))
        super(HostsSshCheckError, self).__init__(message, *args)


class InvalidArgument(ClientException):
    """Invalid argument"""
    pass


class InvalidConfiguration(ClientException):
    """Invalid configuration"""
    pass


class FailedOperation(ClientException):
    pass


class MissingArgument(ClientException):
    """Missing argument"""
    def __init__(self, argname, *args):
        message = (u._('Argument is missing: {name}')
                   .format(name=argname))
        super(MissingArgument, self).__init__(message, *args)
