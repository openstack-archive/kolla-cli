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
from kollacli.common.utils import reraise
from kottos.api.support import SupportApi as KottosSupportApi


class SupportApi(object):

    def support_dump(self, dirpath):
        """Dumps configuration data for debugging.

        Dumps most files in /etc/kolla and /usr/share/kolla into a
        tar file so be given to support / development to help with
        debugging problems.

        :param dirpath: path to directory where dump will be placed
        :type dirpath: string
        :return: path to dump file
        :rtype: string
        """
        try:
            return KottosSupportApi().support_dump(dirpath)
        except Exception as e:
            reraise(e)

    def support_get_logs(self, servicenames, hostname, dirpath):
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
        try:
            KottosSupportApi().support_get_logs(servicenames, hostname,
                                                dirpath)
        except Exception as e:
            reraise(e)
