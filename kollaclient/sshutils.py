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

from kollaclient.utils import get_admin_user
from kollaclient.utils import get_pk_bits
from kollaclient.utils import get_pk_file
from kollaclient.utils import get_pk_password


def ssh_check_keys():
    privateKeyPath = get_pk_file()
    publicKeyPath = privateKeyPath + ".pub"
    if os.path.isfile(privateKeyPath) and os.path.isfile(publicKeyPath):
        return True
    else:
        return False


def ssh_connect(netAddr, username, password, useKeys):
    log = logging.getLogger(__name__)
    try:
        sshClient = paramiko.SSHClient()
        privateKey = ssh_get_private_key()
        sshClient.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        log.info("connecting to addr: " + netAddr +
                 " user: " + username + " password: " + password +
                 " useKeys: " + str(useKeys))
        if useKeys:
            sshClient.connect(hostname=netAddr, username=username,
                              password=password, pkey=privateKey)
        else:
            sshClient.connect(hostname=netAddr, username=username,
                              password=password)

        return sshClient
    except Exception as e:
        # TODO(bmace) better failure behavior here
        log.error("connect exception: " + str(e))
        log.error("connect exception: " + str(type(e)))
        log.error("connect exception: " + str(e.args))
        try:
            sshClient.close()
        except Exception:
            pass
    return None


def ssh_check_host(netAddr):
    log = logging.getLogger(__name__)
    log.info("ssh check connect " + netAddr)
    try:
        sshClient = ssh_connect(netAddr, get_admin_user(), '', True)
        if sshClient is None:
            log.info("check host failed as connect failed")
            return False

        try:
            log.info("about to exec 'ls'")
            sshClient.exec_command("ls")
            return True
            # TODO(bmace) do whatever other checks are needed
        except paramiko.SSHException as sshException:
            log.error("exec failed" + str(sshException))
            log.error("exec failed" + type(sshException))
            log.error("exec failed" + sshException.args)
    except Exception as e:
        # TODO(bmace) better failure behavior here
        log.error(str(e))
        log.error(str(type(e)))
        log.error(str(e.args))
    finally:
        try:
            sshClient.close()
        except Exception:
            pass
    return False


def ssh_install_host(netAddr, password):
    log = logging.getLogger(__name__)
    log.info("ssh install host " + netAddr)
    adminUser = get_admin_user()
    publicKey = ssh_get_public_key()

    try:
        # TODO(bmace) allow setup as some user other than root?
        # add user
        sshClient = ssh_connect(netAddr, "root", password, False)
        commandStr = "useradd -m " + adminUser
        log.info(commandStr)
        stdin, stdout, stderr = sshClient.exec_command(commandStr)
        log.info(str(stdout.read()) + " : " + str(stderr.read()))

        # create ssh dir
        commandStr = ("su - " + adminUser +
                      " -c \"mkdir /home/" + adminUser +
                      "/.ssh\"")
        log.info(commandStr)
        stdin, stdout, stderr = sshClient.exec_command(commandStr)
        log.info(str(stdout.read()) + " : " + str(stderr.read()))

        # create authorized_keys file
        commandStr = ("su - " + adminUser +
                      " -c \"touch /home/" + adminUser +
                      "/.ssh/authorized_keys\"")
        log.info(commandStr)
        stdin, stdout, stderr = sshClient.exec_command(commandStr)
        log.info(str(stdout.read()) + " : " + str(stderr.read()))

        # populate authorized keys file w/ public key
        commandStr = ("su - " + adminUser +
                      " -c \"echo '" + publicKey +
                      "' > /home/" + adminUser +
                      "/.ssh/authorized_keys\"")
        log.info(commandStr)
        stdin, stdout, stderr = sshClient.exec_command(commandStr)
        log.info(str(stdout.read()) + " : " + str(stderr.read()))

        # set appropriate permissions for ssh dir
        commandStr = ("su - " + adminUser +
                      " -c \"chmod 0700 /home/" + adminUser +
                      "/.ssh\"")
        log.info(commandStr)
        stdin, stdout, stderr = sshClient.exec_command(commandStr)
        log.info(str(stdout.read()) + " : " + str(stderr.read()))

        # set appropriate permissions for authorized_keys file
        commandStr = ("su - " + adminUser +
                      " -c \"chmod 0740 /home/" + adminUser +
                      "/.ssh/authorized_keys\"")
        log.info(commandStr)
        stdin, stdout, stderr = sshClient.exec_command(commandStr)
        log.info(str(stdout.read()) + " : " + str(stderr.read()))

        # TODO(bmace) do whatever else needs to be done at install time
    except Exception as e:
        log.error(str(e))
        log.error(str(type(e)))
        log.error(str(e.args()))
    finally:
        try:
            sshClient.close()
        except Exception:
            pass


def ssh_keygen():
    log = logging.getLogger(__name__)

    try:
        privateKeyPath = get_pk_file()
        publicKeyPath = privateKeyPath + ".pub"
        privateKey = None
        privateKeyGenerated = False
        if os.path.isfile(privateKeyPath) is False:
            privateKey = paramiko.RSAKey.generate(get_pk_bits())
            privateKey.write_private_key_file(filename=privateKeyPath,
                                              password=get_pk_password())
            privateKeyGenerated = True
            log.info("generated private key at: " + privateKeyPath)

        # If the public key exists already, only regenerate it if the private
        # key has changed
        if os.path.isfile(publicKeyPath) is False or privateKeyGenerated:
            publicKey = paramiko.RSAKey(filename=privateKeyPath,
                                        password=get_pk_password())
            with open(publicKeyPath, 'w') as pubFile:
                pubFile.write("%s %s" % (publicKey.get_name(),
                              publicKey.get_base64()))
                log.info("generated public key at: " + publicKeyPath)
    except Exception as e:
        # TODO(bmace) better failure behavior here
        log.error(str(e))
        log.error(str(type(e)))
        log.error(str(e.args))


def ssh_get_private_key():
    return paramiko.RSAKey.from_private_key_file(get_pk_file(),
                                                 get_pk_password())


def ssh_get_public_key():
    with open(get_pk_file() + ".pub", "r") as publicKeyFile:
        publicKey = publicKeyFile.read()
        return publicKey
    return None
