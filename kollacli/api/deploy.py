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
from kottos.api.deploy import DeployApi as KottosDeployApi


class DeployApi(object):

    def deploy_set_mode(self, remote_mode):
        """Set deploy mode.

        Set deploy mode to either local or remote. Local indicates
        that the openstack deployment will be to the local host.
        Remote means that the deployment is executed via ssh.

        :param remote_mode: if remote mode is True deployment is done via ssh
        :type remote_mode: bool
        """
        try:
            KottosDeployApi().deploy_set_mode(remote_mode)
        except Exception as e:
            reraise(e)
