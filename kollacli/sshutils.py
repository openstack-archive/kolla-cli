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

from distutils.version import StrictVersion

from kollacli.exceptions import CommandError
from kollacli.utils import get_admin_user
from kollacli.utils import get_setup_user
from kollacli.utils import get_pk_bits
from kollacli.utils import get_pk_file
from kollacli.utils import get_pk_password

MIN_DOCKER_VERSION = '1.7.0'


def ssh_check_keys():
    private_key_path = get_pk_file()
    public_key_path = private_key_path + ".pub"
    if os.path.isfile(private_key_path) and os.path.isfile(public_key_path):
        return True
    else:
        return False


def ssh_connect(net_addr, username, password, useKeys):
    log = logging.getLogger(__name__)
    try:
        logging.getLogger("paramiko").setLevel(logging.WARNING)
        ssh_client = paramiko.SSHClient()
        private_key = ssh_get_private_key()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        log.debug("connecting to addr: " + net_addr +
                  " user: " + username + " password: " + password +
                  " useKeys: " + str(useKeys))
        if useKeys:
            ssh_client.connect(hostname=net_addr, username=username,
                               password=password, pkey=private_key)
        else:
            ssh_client.connect(hostname=net_addr, username=username,
                               password=password)

        return ssh_client
    except Exception as e:
        _close_ssh_client(ssh_client)
        raise e


def ssh_check_host(net_addr):
    log = logging.getLogger(__name__)
    ssh_client = None
    try:
        ssh_client = ssh_connect(net_addr, get_admin_user(), '', True)
        _pre_setup_checks(ssh_client, log)
        _post_setup_checks(net_addr, log)

    finally:
        _close_ssh_client(ssh_client)


def ssh_setup_host(net_addr, password):
    log = logging.getLogger(__name__)
    admin_user = get_admin_user()
    setup_user = get_setup_user()
    public_key = ssh_get_public_key()
    ssh_client = None

    try:
        ssh_client = ssh_connect(net_addr, setup_user, password, False)

        # before modifying the host, check that it meets requirements
        _pre_setup_checks(ssh_client, log)

        # populate authorized keys file w/ public key
        cmd = ('sudo su - %s -c "echo \'%s\' >> $HOME/.ssh/authorized_keys"'
               % (admin_user, public_key, admin_user))
        _exec_ssh_cmd(cmd, ssh_client, log)

        # verify ssh connection to the new account
        _post_setup_checks(net_addr, log)

    except Exception as e:
        raise e
    finally:
        _close_ssh_client(ssh_client)


def _pre_setup_checks(ssh_client, log):
        cmd = 'docker --version'
        msg, errmsg = _exec_ssh_cmd(cmd, ssh_client, log)
        if errmsg:
            raise CommandError("ERROR: '%s' failed. Is docker installed? : %s"
                               % (cmd, errmsg))
        if 'Docker version' not in msg:
            raise CommandError("ERROR: '%s' failed. Is docker installed? : %s"
                               % (cmd, msg))

        version = msg.split('version ')[1].split(',')[0]
        if StrictVersion(version) < StrictVersion(MIN_DOCKER_VERSION):
            raise CommandError('ERROR: docker version (%s) below minimum (%s)'
                               % (version, msg))

        # docker is installed, now check if it is running
        cmd = 'docker info'
        _, errmsg = _exec_ssh_cmd(cmd, ssh_client, log)
        # docker info can return warning messages in stderr, ignore them
        if errmsg and 'WARNING' not in errmsg:
            raise CommandError("ERROR: '%s' failed. Is docker running? : %s"
                               % (cmd, errmsg))

        # check for docker-py
        cmd = 'python -c "import docker"'
        msg, errmsg = _exec_ssh_cmd(cmd, ssh_client, log)
        if errmsg:
            raise CommandError('ERROR: host check failed. ' +
                               'Is docker-py installed?')


def _post_setup_checks(net_addr, log):
    try:
        ssh_client = ssh_connect(net_addr, get_admin_user(), '', True)

    except Exception as e:
        raise CommandError("ERROR: remote login failed : %s" % str(e))

    try:
        # a basic test
        ssh_client.exec_command('ls')

    except Exception as e:
        raise CommandError("ERROR: remote command 'ls' failed : %s" % str(e))

    finally:
        _close_ssh_client(ssh_client)


def _close_ssh_client(ssh_client):
    if ssh_client:
        try:
            ssh_client.close()
        except Exception:
            pass


def ssh_keygen():
    log = logging.getLogger(__name__)

    try:
        private_key_path = get_pk_file()
        public_key_path = private_key_path + ".pub"
        private_key = None
        private_key_generated = False
        if os.path.isfile(private_key_path) is False:
            private_key = paramiko.RSAKey.generate(get_pk_bits())
            private_key.write_private_key_file(filename=private_key_path,
                                               password=get_pk_password())
            private_key_generated = True
            log.info("generated private key at: " + private_key_path)

        # If the public key exists already, only regenerate it if the private
        # key has changed
        if os.path.isfile(public_key_path) is False or private_key_generated:
            public_key = paramiko.RSAKey(filename=private_key_path,
                                         password=get_pk_password())
            with open(public_key_path, 'w') as pubFile:
                pubFile.write("%s %s" % (public_key.get_name(),
                                         public_key.get_base64()))
                log.info("generated public key at: " + public_key_path)
    except Exception as e:
        raise e


def _exec_ssh_cmd(cmd, ssh_client, log):
    log.debug(cmd)
    _, stdout, stderr = ssh_client.exec_command(cmd, get_pty=True)
    msg = stdout.read()
    errmsg = stderr.read()
    log.debug('%s : %s' % (msg, errmsg))
    if errmsg:
        log.warn('WARNING: command (%s) message : %s' % (cmd, errmsg.strip()))
    return msg, errmsg


def ssh_get_private_key():
    return paramiko.RSAKey.from_private_key_file(get_pk_file(),
                                                 get_pk_password())


def ssh_get_public_key():
    with open(get_pk_file() + ".pub", "r") as public_key_file:
        public_key = public_key_file.read()
        return public_key
    return None
