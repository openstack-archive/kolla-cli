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
import kollacli.i18n as u

import logging
import os
import sys

from logging.handlers import RotatingFileHandler

from kollacli.api.control_plane import ControlPlaneApi
from kollacli.api.group import GroupApi
from kollacli.api.host import HostApi
from kollacli.api.password import PasswordApi
from kollacli.api.properties import PropertyApi
from kollacli.api.service import ServiceApi
from kollacli.api.support import SupportApi
from kollacli.common.utils import get_log_level

CONSOLE_MESSAGE_FORMAT = '%(message)s'
LOG_FILE_MESSAGE_FORMAT = \
    '[%(asctime)s] %(levelname)-8s %(name)s %(message)s'
LOG = None

VERSION = '2.0'


class ClientApi(
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

    def __init__(self):
        self._configure_logging()

    @staticmethod
    def get_version():
        # type: () -> str
        return VERSION

    @staticmethod
    def base_call():
        LOG.info('base call')

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

    def _configure_logging(self):
        global LOG
        root_logger = logging.getLogger('')
        root_logger.setLevel(logging.DEBUG)

        handler_found = False
        handlers = root_logger.handlers
        for handler in handlers:
            if isinstance(handler, RotatingFileHandler):
                handler_found = True
                break
        if not handler_found:
            # logger has not been set up
            try:
                rotate_handler = RotatingFileHandler(
                    os.path.join(os.path.abspath(os.sep),
                                 'var', 'log', 'kolla', 'kolla.log'),
                    maxBytes=self._get_kolla_log_file_size(),
                    backupCount=4)

            except IOError as e:
                # most likely the caller is not part of the kolla group
                raise IOError(u._('Permission denied to run the kolla client.'
                                  '\nPlease add user to the kolla group and '
                                  'then log out and back in. {error}')
                              .format(error=str(e)))

            formatter = logging.Formatter(LOG_FILE_MESSAGE_FORMAT)
            rotate_handler.setFormatter(formatter)
            rotate_handler.setLevel(get_log_level())
            root_logger.addHandler(rotate_handler)
            LOG = logging.getLogger(__name__)

    def _get_kolla_log_file_size(self):
        # type: () -> int
        envvar = 'KOLLA_LOG_FILE_SIZE'
        size_str = os.environ.get(envvar, '500000')
        try:
            size = int(size_str)
        except Exception:
            size = 50000
        return size
