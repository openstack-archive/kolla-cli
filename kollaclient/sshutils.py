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
    log.info("ssh connect " + netAddr)
    try:
        sshClient = paramiko.SSHClient()
        privateKey = ssh_get_private_key()
        sshClient.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        if useKeys:
            sshClient.connect(hostname=netAddr, username=username,
                              password=password, pkey=privateKey)
        else:
            sshClient.connect(hostname=netAddr, username=username,
                              password=password, pkey=None)
    except Exception as e:
        # TODO(bmace) better failure behavior here
        log.error(e)
        log.error(type(e))
        log.error(e.args)
        sshClient.close()
    return sshClient


def ssh_check_connect(netAddr):
    log = logging.getLogger(__name__)
    log.info("ssh check connect " + netAddr)
    try:
        sshClient = ssh_connect(netAddr, get_admin_user(), '', True)
        try:
            sshClient.exec_command("ls")
            return True
        except paramiko.SSHException as sshException:
            log.error("exec failed" + sshException)
            log.error("exec failed" + type(sshException))
            log.error("exec failed" + sshException.args)
            sshClient.close()
            return False
    except Exception as e:
        # TODO(bmace) better failure behavior here
        log.error(e)
        log.error(type(e))
        log.error(e.args)
        sshClient.close()


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
        log.error(e)
        log.error(type(e))
        log.error(e.args)


def ssh_get_private_key():
    return paramiko.RSAKey.from_private_key_file(get_pk_file(),
                                                 get_pk_password())
