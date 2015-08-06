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

from kollacli.utils import get_admin_user
from kollacli.utils import get_pk_bits
from kollacli.utils import get_pk_file
from kollacli.utils import get_pk_password


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
        try:
            ssh_client.close()
        except Exception:
            pass
        raise e


def ssh_check_host(net_addr):
    try:
        ssh_client = ssh_connect(net_addr, get_admin_user(), '', True)
        ssh_client.exec_command("ls")
        # TODO(bmace) do whatever other checks are needed
    except Exception as e:
        raise e
    finally:
        try:
            ssh_client.close()
        except Exception:
            pass


def ssh_install_host(net_addr, password):
    log = logging.getLogger(__name__)
    admin_user = get_admin_user()
    publicKey = ssh_get_public_key()

    try:
        # TODO(bmace) allow setup as some user other than root?
        # add user
        ssh_client = ssh_connect(net_addr, "root", password, False)
        command_str = "useradd -m " + admin_user
        log.debug(command_str)
        _, stdout, stderr = ssh_client.exec_command(command_str)
        log.debug(str(stdout.read()) + " : " + str(stderr.read()))

        # create ssh dir
        command_str = ("su - " + admin_user +
                       " -c \"mkdir /home/" + admin_user +
                       "/.ssh\"")
        log.debug(command_str)
        _, stdout, stderr = ssh_client.exec_command(command_str)
        log.debug(str(stdout.read()) + " : " + str(stderr.read()))

        # create authorized_keys file
        command_str = ("su - " + admin_user +
                       " -c \"touch /home/" + admin_user +
                       "/.ssh/authorized_keys\"")
        log.debug(command_str)
        _, stdout, stderr = ssh_client.exec_command(command_str)
        log.debug(str(stdout.read()) + " : " + str(stderr.read()))

        # populate authorized keys file w/ public key
        command_str = ("su - " + admin_user +
                       " -c \"echo '" + publicKey +
                       "' > /home/" + admin_user +
                       "/.ssh/authorized_keys\"")
        log.debug(command_str)
        _, stdout, stderr = ssh_client.exec_command(command_str)
        log.debug(str(stdout.read()) + " : " + str(stderr.read()))

        # set appropriate permissions for ssh dir
        command_str = ("su - " + admin_user +
                       " -c \"chmod 0700 /home/" + admin_user +
                       "/.ssh\"")
        log.debug(command_str)
        _, stdout, stderr = ssh_client.exec_command(command_str)
        log.debug(str(stdout.read()) + " : " + str(stderr.read()))

        # set appropriate permissions for authorized_keys file
        command_str = ("su - " + admin_user +
                       " -c \"chmod 0740 /home/" + admin_user +
                       "/.ssh/authorized_keys\"")
        log.debug(command_str)
        _, stdout, stderr = ssh_client.exec_command(command_str)
        log.debug(str(stdout.read()) + " : " + str(stderr.read()))

        # TODO(bmace) do whatever else needs to be done at install time
    except Exception as e:
        raise e
    finally:
        try:
            ssh_client.close()
        except Exception:
            pass


def ssh_uninstall_host(net_addr):
    log = logging.getLogger(__name__)
    admin_user = get_admin_user()

    try:
        ssh_client = ssh_connect(net_addr, get_admin_user(), '', True)

        # delete user
        command_str = 'userdel %s' % admin_user
        log.debug(command_str)
        _, stdout, stderr = ssh_client.exec_command(command_str)
        log.debug(str(stdout.read()) + " : " + str(stderr.read()))

        # remove directory and files
        command_str = 'rm -rf /home/%s' % admin_user
        log.debug(command_str)
        _, stdout, stderr = ssh_client.exec_command(command_str)
        log.debug(str(stdout.read()) + " : " + str(stderr.read()))

        # TODO(snoyes) do whatever else needs to be done at uninstall time
    except Exception as e:
        raise e
    finally:
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


def ssh_get_private_key():
    return paramiko.RSAKey.from_private_key_file(get_pk_file(),
                                                 get_pk_password())


def ssh_get_public_key():
    with open(get_pk_file() + ".pub", "r") as publicKeyFile:
        publicKey = publicKeyFile.read()
        return publicKey
    return None
