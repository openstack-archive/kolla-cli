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
import logging
import traceback

from cliff.command import Command

from kolla_cli.api.client import ClientApi

CLIENT = ClientApi()
LOG = logging.getLogger(__name__)


class ConfigReset(Command):
    """Resets the kolla-ansible configuration to its release defaults."""

    def take_action(self, parsed_args):
        try:
            CLIENT.config_reset()
        except Exception:
            raise Exception(traceback.format_exc())
