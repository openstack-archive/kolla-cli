import logging
import paramiko

from kollaclient.utils import get_pk_bits
from kollaclient.utils import get_pk_file
from kollaclient.utils import get_pk_password


def ssh_connect(hostname):

    log = logging.getLogger(__name__)

    log.info("ssh connect " + hostname)
    # ssh = paramiko.SSHClient()
    # privateKey = paramiko.RSAKey.from_private_key_file(get_pk_file())
    # ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    return


def ssh_keygen():

    log = logging.getLogger(__name__)

    try:
        log.info("keygen")
        privateKey = paramiko.RSAKey.generate(get_pk_bits())
        log.info("writekey")
        privateKey.write_private_key_file(filename=get_pk_file(),
                                          password=get_pk_password())
        log.info("genpubkey")
        publicKey = paramiko.RSAKey(filename=get_pk_file(),
                                    password=get_pk_password())
        log.info("writepubkey")
        with open("%s.pub" % get_pk_file(), 'w') as pubFile:
            pubFile.write("%s %s" % (publicKey.get_name(),
                          publicKey.get_base64()))
        log.info("donekeygen")
    except Exception as e:
        print e
        print type(e)
        print e.args
