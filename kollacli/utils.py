# Copyright(c) 2015, Oracle and/or its affiliates.  All Rights Reserved.
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
import yaml


def get_kolla_home():
    return os.environ.get("KOLLA_HOME", "/opt/kolla/")


def get_kolla_etc():
    return os.environ.get("KOLLA_ETC", "/etc/kolla/")


def get_kollacli_home():
    return os.environ.get("KOLLA_CLI_HOME", "/opt/kollacli/")


def get_kollacli_etc():
    return os.environ.get("KOLLA_CLI_ETC", "/etc/kolla/kollacli/")


def get_admin_user():
    return os.environ.get("KOLLA_CLI_ADMIN_USER", "kolla")


def get_pk_file():
    return os.environ.get("KOLLA_CLI_PKPATH",
                          "/etc/kolla/kollacli/etc/id_rsa")


def get_pk_password():
    # TODO(bmace) what to do here? pull from a file?
    return None


def get_pk_bits():
    return 1024


def load_etc_yaml(fileName):
    contents = {}
    try:
        with open(get_kollacli_etc() + fileName, 'r') as f:
            contents = yaml.load(f)
    except Exception:
        # TODO(bmace) if file doesn't exist on a load we don't
        # want to blow up, some better behavior here?
        pass
    return contents or {}


def save_etc_yaml(fileName, contents):
    with open(get_kollacli_etc() + fileName, 'w') as f:
        f.write(yaml.dump(contents))
