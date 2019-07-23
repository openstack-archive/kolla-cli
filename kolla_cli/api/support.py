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

from kolla_cli.api.exceptions import InvalidArgument
from kolla_cli.common.support import dump
from kolla_cli.common.support import get_logs
from kolla_cli.common.utils import check_arg
from kolla_cli.common.utils import safe_decode
import kolla_cli.i18n as u

MYPY = False
if MYPY:
    from typing import List  # noqa


class SupportApi(object):

    def support_dump(self, dirpath):
        # type: (str) -> str
        """Dumps configuration data for debugging.

        Dumps most files in /etc/kolla and /usr/share/kolla into a
        tar file so be given to support / development to help with
        debugging problems.

        :param dirpath: path to directory where dump will be placed
        :type dirpath: string
        :return: path to dump file
        :rtype: string
        """
        check_arg(dirpath, u._('Directory path'), str)
        dirpath = safe_decode(dirpath)
        if not os.path.exists(dirpath):
            raise InvalidArgument(u._('Directory path: {path} does not exist')
                                  .format(path=dirpath))
        dumpfile_path = dump(dirpath)
        return dumpfile_path

    def support_get_logs(self, servicenames, hostname, dirpath):
        # type: (List[str], str, str) -> None
        """get container logs

        Fetch the container log files of services from the specified hosts.
        The log files will be placed in the named directory. All the containers
        for the host will be placed in a directory named hostname. The file
        names for each log will be servicename_id.log.

        :param servicenames: names of services (ie nova, glance, etc)
        :type servicenames: list of strings
        :param hostname: name of host to look for logs on
        :type hostname: string
        :param dirpath: path of directory where log files will be written
        :type dirpath: string
        """
        check_arg(dirpath, u._('Directory path'), str)
        dirpath = safe_decode(dirpath)
        if not os.path.exists(dirpath):
            raise InvalidArgument(u._('Directory path: {path} does not exist')
                                  .format(path=dirpath))

        check_arg(servicenames, u._('Service names'), list)
        servicenames = safe_decode(servicenames)
        check_arg(hostname, u._('Host names'), str)
        hostname = safe_decode(hostname)

        get_logs(servicenames, hostname, dirpath)
