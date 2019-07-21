# Copyright(c) 2018, Oracle and/or its affiliates.  All Rights Reserved.
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

from kolla_cli.api.job import Job
from kolla_cli.common.ansible.actions import KollaAction
from kolla_cli.common.utils import check_arg
import kolla_cli.i18n as u


class CertificateApi(object):

    @staticmethod
    def certificate_init(verbose_level=1):
        """Certificate Init.

        Creates a self-signed certificate for secure TLS communication.

        :param verbose_level: the higher the number, the more verbose
        :type verbose_level: integer
        :return: Job object
        :rtype: Job
        """
        check_arg(verbose_level, u._('Verbose level'), int)
        action = KollaAction(verbose_level=verbose_level,
                             playbook_name='certificates.yml')
        ansible_job = action.certificate_init()
        return Job(ansible_job)
