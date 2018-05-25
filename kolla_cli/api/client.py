# Copyright(c) 2017, Oracle and/or its affiliates.  All Rights Reserved.
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

import logging
import sys

from kolla_cli.api.certificate import CertificateApi
from kolla_cli.api.config import ConfigApi
from kolla_cli.api.control_plane import ControlPlaneApi
from kolla_cli.api.group import GroupApi
from kolla_cli.api.host import HostApi
from kolla_cli.api.password import PasswordApi
from kolla_cli.api.properties import PropertyApi
from kolla_cli.api.service import ServiceApi
from kolla_cli.api.support import SupportApi

CONSOLE_MESSAGE_FORMAT = '%(message)s'

# TODO(bmace) - API version should probably be stored somewhere else
VERSION = '0.1'


class ClientApi(
        CertificateApi,
        ConfigApi,
        ControlPlaneApi,
        GroupApi,
        HostApi,
        PasswordApi,
        PropertyApi,
        ServiceApi,
        SupportApi,
        ):
    """Client API Notes

    Objects returned by the API contain a local copy of the information
    in the datastore. While changes made to the local copy will be
    reflected in the local object, changes made to the datastore
    from other objects will not be reflected in this local copy. The
    object will need to be re-fetched from the datastore to reflect
    the updates.
    """

    @staticmethod
    def get_version():
        # type: () -> str
        return VERSION

    @staticmethod
    def enable_console_logging(level, enable=True):
        # type: (int, bool) -> None
        """enable/disable console logging for the api

        enable: True/False
        level: logging.INFO, logging.DEBUG, logging.WARNING,
        logging.CRITICAL...
        """
        root_logger = logging.getLogger('')
        console = logging.StreamHandler(sys.stderr)
        if enable:
            console.setLevel(level)
            formatter = logging.Formatter(CONSOLE_MESSAGE_FORMAT)
            console.setFormatter(formatter)
            root_logger.addHandler(console)
        else:
            root_logger.removeHandler(console)
