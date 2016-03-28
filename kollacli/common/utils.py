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
import fcntl
import grp
import logging
import os
import pexpect
import pwd
import six
import sys

import kollacli.i18n as u

from kollacli.api.exceptions import InvalidArgument
from kollacli.api.exceptions import MissingArgument

LOG = logging.getLogger(__name__)


def get_kolla_home():
    return os.environ.get("KOLLA_HOME", "/usr/share/kolla/")


def get_kolla_etc():
    return os.environ.get("KOLLA_ETC", "/etc/kolla/")


def get_kollacli_home():
    return os.environ.get("KOLLA_CLI_HOME", "/usr/share/kolla/kollacli/")


def get_kollacli_etc():
    return os.environ.get("KOLLA_CLI_ETC", "/etc/kolla/kollacli/")


def get_group_vars_dir():
    return os.path.join(get_kolla_home(), 'ansible/group_vars')


def get_host_vars_dir():
    return os.path.join(get_kolla_home(), 'ansible/host_vars')


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
        raise InvalidArgument(
            u._('Environmental variable ({env_var}) is not an '
                'integer ({log_size}).')
            .format(env_var=envvar, log_size=size_str))
    return size


def get_property_list_length():
    envvar = 'KOLLA_PROP_LIST_LENGTH'
    length_str = os.environ.get(envvar, '50')
    try:
        length = int(length_str)
    except Exception:
        raise InvalidArgument(
            u._('Environmental variable ({env_var}) is not an '
                'integer ({prop_length}).')
            .format(env_var=envvar, prop_length=length_str))
    return length


def get_admin_user():
    return os.environ.get("KOLLA_CLI_ADMIN_USER", "kolla")


def get_setup_user():
    return os.environ.get("KOLLA_CLI_SETUP_USER", "root")


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
                suffix = fname.split('.')[1]
                if suffix.isdigit():
                    py2_path = os.path.join(usr_bin, fname)
                    break
        if py2_path is None:
            raise Exception(
                u._('ansible-playbook requires python2 and no '
                    'python2 interpreter found in {path}.')
                .format(path=usr_bin))
        cmd = '%s %s' % (py2_path, os.path.join(usr_bin, cmd))
    return cmd


def convert_to_unicode(the_string):
    """convert string to unicode.

    This is used to fixup extended ascii chars in strings. these chars cause
    errors in json pickle/unpickle.
    """
    if the_string is None:
        return the_string
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
                u._('Insufficient permissions to run command "{command}".')
                .format(command=cmd))
        child.maxsize = 1
        child.timeout = 86400
        for line in child:
            line = safe_decode(line)
            outline = sniff + line.rstrip()
            sniff = ''
            output = ''.join([output, outline, '\n'])
            if print_output:
                LOG.info(outline)

    except Exception as e:
        err_msg = '%s' % e
    finally:
        if child:
            child.close()
            if child.exitstatus != 0:
                err_msg = (u._('Command failed. : {error}')
                           .format(error=err_msg))
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
        group_info = grp.getgrnam('kolla')
        if not os.path.exists(file_path):
            with open(file_path, 'a'):
                os.utime(file_path, None)
                os.chown(file_path, -1, group_info.gr_gid)

        new_contents = []
        read_data = sync_read_file(file_path)
        lines = read_data.split('\n')
        new_line = '%s: "%s"' % (property_key, property_value)
        property_key_found = False
        last_line_empty = False
        for line in lines:
            line = line.rstrip()

            # yank spurious empty lines
            if line:
                last_line_empty = False
            else:
                if last_line_empty:
                    continue
                last_line_empty = True

            split_line = line.split(':', 1)
            if len(split_line) > 1:
                split_key = split_line[0]
                split_key.rstrip()
                if split_key == property_key:
                    property_key_found = True
                    if clear:
                        # clear existing property
                        continue
                    # edit existing property
                    line = new_line
            new_contents.append(line)
        if not property_key_found and not clear:
            # add new property to file
            new_contents.append(new_line)

        write_data = '\n'.join(new_contents)
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


def safe_decode(obj_to_decode):
    """Convert bytes or string to unicode string

    Convert either a string or list of strings to
    unicode.
    """
    if obj_to_decode is None:
        return None

    new_obj = None
    if isinstance(obj_to_decode, list):
        new_obj = []
        for text in obj_to_decode:
            try:
                text = text.decode('utf-8')
            except AttributeError:   # nosec
                # py3 will raise if text is already a string
                pass
            new_obj.append(text)
    else:
        try:
            new_obj = obj_to_decode.decode('utf-8')
        except AttributeError:   # nosec
            # py3 will raise if text is already a string
            new_obj = obj_to_decode
    return new_obj


def is_string_true(string):
    """Return boolean True if string represents a true value (None is False)"""
    true_values = ['yes', 'true']
    if string is not None and string.lower() in true_values:
        return True
    else:
        return False


def check_arg(param, param_name, expected_type, none_ok=False, empty_ok=False):
    if param is None:
        if none_ok:
            return
        # None arg
        raise MissingArgument(param_name)

    if ((isinstance(param, str) or
            isinstance(param, dict) or
            isinstance(param, list)) and
            not param and not empty_ok):
        # empty string, dict or list
        raise MissingArgument(param_name)

    if not isinstance(param, expected_type):
        # wrong type
        raise InvalidArgument(u._('{name} ({param}) is not a {type}')
                              .format(name=param_name, param=param,
                                      type=expected_type))
