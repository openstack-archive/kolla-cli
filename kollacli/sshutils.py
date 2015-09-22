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
import logging
import os.path
import paramiko
import traceback

from distutils.version import StrictVersion

from kollacli.exceptions import CommandError
from kollacli.utils import get_admin_user
from kollacli.utils import get_kollacli_etc
from kollacli.utils import get_setup_user

MIN_DOCKER_VERSION = '1.8.1'


def ssh_connect(net_addr, username, password):
    try:
        logging.getLogger('paramiko').setLevel(logging.WARNING)
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh_client.connect(hostname=net_addr, username=username,
                           password=password)
        return ssh_client
    except Exception:
        _close_ssh_client(ssh_client)
        raise Exception(traceback.format_exc())


def ssh_setup_host(net_addr, password):
    log = logging.getLogger(__name__)
    admin_user = get_admin_user()
    setup_user = get_setup_user()
    public_key = ssh_get_public_key()
    ssh_client = None

    try:
        ssh_client = ssh_connect(net_addr, setup_user, password)

        # before modifying the host, check that it meets requirements
        # TODO(bmace) pre / post checks should be done with ansible

        # populate authorized keys file w/ public key
        cmd = ('sudo su - %s -c "echo \'%s\' >> %s/.ssh/authorized_keys"'
               % (admin_user, public_key, os.path.expanduser('~kolla')))
        _exec_ssh_cmd(cmd, ssh_client, log)

        # TODO(bmace) verify ssh connection to the new account
    except Exception as e:
        raise e
    finally:
        _close_ssh_client(ssh_client)


def _pre_setup_checks(ssh_client, log):
        cmd = 'docker --version'
        msg, errmsg = _exec_ssh_cmd(cmd, ssh_client, log)
        if errmsg:
            raise CommandError("'%s' failed. Is docker installed? : %s"
                               % (cmd, errmsg))
        if 'Docker version' not in msg:
            raise CommandError("'%s' failed. Is docker installed? : %s"
                               % (cmd, msg))

        version = msg.split('version ')[1].split(',')[0]
        if StrictVersion(version) < StrictVersion(MIN_DOCKER_VERSION):
            raise CommandError('docker version (%s) below minimum (%s)'
                               % (version, msg))

        # docker is installed, now check if it is running
        cmd = 'docker info'
        _, errmsg = _exec_ssh_cmd(cmd, ssh_client, log)
        # docker info can return warning messages in stderr, ignore them
        if errmsg and 'WARNING' not in errmsg:
            raise CommandError("'%s' failed. Is docker running? : %s"
                               % (cmd, errmsg))

        # check for docker-py
        cmd = 'python -c "import docker"'
        msg, errmsg = _exec_ssh_cmd(cmd, ssh_client, log)
        if errmsg:
            raise CommandError('host check failed. ' +
                               'Is docker-py installed?')


def _post_setup_checks(net_addr, log):
    try:
        ssh_client = ssh_connect(net_addr, get_admin_user(), '')

    except Exception as e:
        raise CommandError("remote login failed : %s" % e)

    try:
        # a basic test
        ssh_client.exec_command('ls')

    except Exception as e:
        raise CommandError("remote command 'ls' failed : %s" % e)

    finally:
        _close_ssh_client(ssh_client)


def _close_ssh_client(ssh_client):
    if ssh_client:
        try:
            ssh_client.close()
        except Exception:
            pass


def _exec_ssh_cmd(cmd, ssh_client, log):
    log.debug(cmd)
    _, stdout, stderr = ssh_client.exec_command(cmd, get_pty=True)
    msg = stdout.read()
    errmsg = stderr.read()
    log.debug('%s : %s' % (msg, errmsg))
    if errmsg:
        log.warn('WARNING: command (%s) message : %s' % (cmd, errmsg.strip()))
    return msg, errmsg


def ssh_get_public_key():
    keyfile_path = os.path.join(get_kollacli_etc(), 'id_rsa.pub')
    with open(keyfile_path, "r") as public_key_file:
        public_key = public_key_file.read()
        return public_key
    return None
