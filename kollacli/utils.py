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
import fcntl
import logging
import os
import pexpect
import pwd
import six
import sys
import yaml

from kollacli.exceptions import CommandError
from oslo_utils.encodeutils import safe_decode


def get_kolla_home():
    return os.environ.get("KOLLA_HOME", "/usr/share/kolla/")


def get_kolla_etc():
    return os.environ.get("KOLLA_ETC", "/etc/kolla/")


def get_kollacli_home():
    return os.environ.get("KOLLA_CLI_HOME", "/usr/share/kolla/kollacli/")


def get_kollacli_etc():
    return os.environ.get("KOLLA_CLI_ETC", "/etc/kolla/kollacli/")


def get_kolla_log_dir():
    return '/var/log/kolla/'


def get_admin_uids():
    """get uid and gid of admin user"""
    user_info = pwd.getpwnam(get_admin_user())
    uid = user_info.pw_uid
    gid = user_info.pw_gid
    return uid, gid


def get_kolla_log_file_size():
    envvar = 'KOLLA_LOG_FILE_SIZE'
    size_str = os.environ.get(envvar, '500000')
    try:
        size = int(size_str)
    except Exception:
        raise CommandError('Environmental variable ' +
                           '(%s) is not an integer' % (envvar, size_str))
    return size


def get_admin_user():
    return os.environ.get("KOLLA_CLI_ADMIN_USER", "kolla")


def get_setup_user():
    return os.environ.get("KOLLA_CLI_SETUP_USER", "root")


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


def get_ansible_command(playbook=False):
    """get a python2 ansible command

    Ansible cannot run yet with python3. If the current default
    python is py3, prefix the ansible command with a py2
    interpreter.
    """
    cmd = 'ansible'
    if playbook:
        cmd = 'ansible-playbook'
    if sys.version_info[0] >= 3:
        # running with py3, find a py2 interpreter for ansible
        py2_path = None
        usr_bin = os.path.join('/', 'usr', 'bin')
        for fname in os.listdir(usr_bin):
            if (fname.startswith('python2.') and
                    os.path.isfile(os.path.join(usr_bin, fname))):
                suffix = file.split('.')[1]
                if suffix.isdigit():
                    py2_path = os.path.join(usr_bin, fname)
                    break
        if py2_path is None:
            raise Exception('ansible-playbook requires python2 and no '
                            'python2 interpreter found in %s' % usr_bin)
        cmd = '%s %s' % (py2_path, os.path.join(usr_bin, cmd))
    return cmd


def convert_to_unicode(the_string):
    """convert string to unicode.

    This is used to fixup extended ascii chars in strings. these chars cause
    errors in json pickle/unpickle.
    """
    return six.u(the_string)


def run_cmd(cmd, print_output=True):
    """run a system command

    return:
    - err_msg:  empty string=command succeeded
                not None=command failed
    - output:   string: all the output of the run command

    If the command is an ansible playbook command, record the
    output in an ansible log file.
    """
    pwd_prompt = '[sudo] password'
    log = logging.getLogger(__name__)
    err_msg = ''
    output = ''
    child = None
    try:
        child = pexpect.spawn(cmd)
        sniff = child.read(len(pwd_prompt))
        sniff = safe_decode(sniff)
        if sniff == pwd_prompt:
            output = sniff + '\n'
            raise Exception(
                'Insufficient permissions to run command "%s"' % cmd)
        child.maxsize = 1
        child.timeout = 86400
        for line in child:
            line = safe_decode(line)
            outline = sniff + line.rstrip()
            sniff = ''
            output = ''.join([output, outline, '\n'])
            if print_output:
                log.info(outline)

    except Exception as e:
        err_msg = '%s' % e
    finally:
        if child:
            child.close()
            if child.exitstatus != 0:
                err_msg = 'Command Failed %s' % err_msg
    return err_msg, output


def change_property(file_path, property_key, property_value, clear=False):
    """change property with a file

    file_path:         path to property file
    property_key:      property name
    property value:    property value
    clear:             flag to remove property

    If clear, and property exists, remove it from the property file.
    If clear, and property doesn't exists, nothing is done.
    If not clear, and key is not found, the new property will be appended.
    If not clear, and key is found, edit property in place.
    """
    try:
        new_contents = []
        read_data = sync_read_file(file_path)
        lines = read_data.split('\n')
        new_line = '%s: "%s"\n' % (property_key, property_value)
        property_key_found = False
        for line in lines:
            if line[0:len(property_key)] == property_key:
                property_key_found = True
                if clear:
                    # clear existing property
                    line = ''
                else:
                    # edit existing property
                    line = new_line
            new_contents.append(line + '\n')
        if not property_key_found and not clear:
            # add new property to file
            new_contents.append(new_line)

        write_data = ''.join(new_contents)
        sync_write_file(file_path, write_data)

    except Exception as e:
        raise e


def sync_read_file(path, mode='r'):
    """synchronously read file

    return file data
    """
    try:
        with open(path, mode) as data_file:
            fcntl.flock(data_file, fcntl.LOCK_EX)
            data = data_file.read()
    except Exception as e:
        raise e
    return data


def sync_write_file(path, data, mode='w'):
    """synchronously write file"""
    try:
        with open(path, mode) as data_file:
            fcntl.flock(data_file, fcntl.LOCK_EX)
            data_file.write(data)
    except Exception as e:
        raise e
