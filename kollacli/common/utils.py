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

import blaze.api.exceptions
import kollacli.api.exceptions
import kollacli.i18n as u


def reraise(exception):
    """convert mesos exception to cli exception

    This is a temporary measure until the rest api is available.
    """
    if isinstance(exception, blaze.api.exceptions.FailedOperation):
        raise kollacli.api.exceptions.FailedOperation(exception)
    elif isinstance(exception, blaze.api.exceptions.HostError):
        raise kollacli.api.exceptions.HostError(exception)
    elif isinstance(exception,
                    blaze.api.exceptions.HostsSshCheckError):
        raise kollacli.api.exceptions.HostsSshCheckError(exception)
    elif isinstance(exception, blaze.api.exceptions.InvalidArgument):
        raise kollacli.api.exceptions.InvalidArgument(exception)
    elif isinstance(exception,
                    blaze.api.exceptions.InvalidConfiguration):
        raise kollacli.api.exceptions.InvalidConfiguration(exception)
    elif isinstance(exception, blaze.api.exceptions.MissingArgument):
        raise kollacli.api.exceptions.MissingArgument(exception)
    elif isinstance(exception, blaze.api.exceptions.NotInInventory):
        raise kollacli.api.exceptions.NotInInventory(exception)
    raise exception


def safe_decode(obj_to_decode):
    """Convert bytes or strings to unicode string

    Converts strings, lists, or dictionaries to
    unicode.
    """
    if obj_to_decode is None:
        return None

    new_obj = None
    if isinstance(obj_to_decode, list):
        new_obj = []
        for text in obj_to_decode:
            text = safe_decode(text)
            new_obj.append(text)
    elif isinstance(obj_to_decode, dict):
        new_obj = {}
        for key, value in obj_to_decode.items():
            key = safe_decode(key)
            value = safe_decode(value)
            new_obj[key] = value

    else:
        try:
            new_obj = obj_to_decode.decode('utf-8')
        except AttributeError:   # nosec
            # py3 will raise if text is already a string
            new_obj = obj_to_decode
    return new_obj


def get_property_list_length():
    envvar = 'KOLLA_PROP_LIST_LENGTH'
    length_str = os.environ.get(envvar, '50')
    try:
        length = int(length_str)
    except Exception:
        raise Exception(
            u._('Environmental variable ({env_var}) is not an '
                'integer ({prop_length}).')
            .format(env_var=envvar, prop_length=length_str))
    return length
