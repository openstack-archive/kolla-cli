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

import logging
import os.path
import paramiko
import traceback

from kolla_cli.common.utils import get_admin_user
from kolla_cli.common.utils import get_kolla_cli_etc
from kolla_cli.common.utils import get_setup_user
import kolla_cli.i18n as u

MIN_DOCKER_VERSION = '1.10.0'

LOG = logging.getLogger(__name__)


def ssh_connect(net_addr, username, password):
    try:
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh_client.connect(hostname=net_addr, username=username,
                           password=password)
        return ssh_client
    except Exception:
        _close_ssh_client(ssh_client)
        raise Exception(traceback.format_exc())


def ssh_setup_host(net_addr, password, setup_user=None):
    admin_user = get_admin_user()
    if setup_user is None:
        setup_user = get_setup_user()
    public_key = ssh_get_public_key()
    ssh_client = None

    try:
        ssh_client = ssh_connect(net_addr, setup_user, password)
        # populate authorized keys file w/ public key
        key_dir = os.path.join(os.path.expanduser('~%s' % admin_user),
                               '.ssh', 'authorized_keys')
        cmd = ('/usr/bin/sudo su - %s -c "echo \'%s\' >> %s"'
               % (admin_user, public_key, key_dir))
        _exec_ssh_cmd(cmd, ssh_client)
    except Exception as e:
        raise e
    finally:
        _close_ssh_client(ssh_client)


def _close_ssh_client(ssh_client):
    if ssh_client:
        try:
            ssh_client.close()
        except Exception:  # nosec
            pass


def _exec_ssh_cmd(cmd, ssh_client):
    LOG.debug(cmd)
    _, stdout, stderr = ssh_client.exec_command(cmd, get_pty=True)  # nosec
    msg = stdout.read()
    errmsg = stderr.read()
    LOG.debug('%s : %s' % (msg, errmsg))
    if errmsg:
        LOG.warn(
            u._LW('WARNING: command : {command})\nmessage : {message}')
            .format(command=cmd, message=errmsg.strip()))
    return msg, errmsg


def ssh_get_public_key():
    keyfile_path = os.path.join(get_kolla_cli_etc(), 'id_rsa.pub')
    with open(keyfile_path, "r") as public_key_file:
        public_key = public_key_file.read()
        return public_key
