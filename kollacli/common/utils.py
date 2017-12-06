# Copyright(c) 2017, Oracle and/or its affiliates.  All Rights Reserved.
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
import copy
import fcntl
import grp
import logging
import os
import pwd
import six
import subprocess  # nosec
import sys
import time
import yaml

import kollacli.i18n as u

from kollacli.api.exceptions import InvalidArgument
from kollacli.api.exceptions import MissingArgument

LOG = logging.getLogger(__name__)


def get_log_level():
    evar = os.environ.get('KOLLA_LOG_LEVEL', 'info')
    if evar.lower() == 'debug':
        level = logging.DEBUG
    else:
        level = logging.INFO
    return level


def get_ansible_plugin_dir():
    return os.environ.get("ANSIBLE_PLUGINS",
                          "/usr/share/ansible/plugins/callback/")


def get_ansible_etc():
    return os.environ.get("ANSIBLE_ETC",
                          "/etc/ansible/")


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


def get_ansible_lock_path():
    return os.path.join(get_kollacli_home(), 'ansible.lock')


def get_kolla_actions_path():
    return os.path.join(get_kollacli_home(), 'tools', 'kolla_actions.py')


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


def get_lock_enabled():
    evar = os.environ.get('KOLLA_CLI_LOCK', 'true')
    if evar.lower() == 'false':
        return False
    else:
        return True


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
    """
    err = None
    output = None
    try:
        process = subprocess.Popen(cmd, shell=True,  # nosec
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        output, err = process.communicate()
    except Exception as e:
        err = str(e)

    err = safe_decode(err)
    output = safe_decode(output)
    if process.returncode != 0:
        err = (u._('Command failed. : {error}')
               .format(error=err))
    if print_output:
        LOG.info(output)
    return err, output


def change_password(file_path, pname, pvalue=None, public_key=None,
                    private_key=None, clear=False):
    """change password in passwords.yml file

    file_path:         path to passwords file
    pname:             name of password
    pvalue:            value of password when not ssh key
    public_key:        public ssh key
    private_key:       private ssh key
    clear:             flag to remove password

    If clear, and password exists, remove it from the password file.
    If clear, and password doesn't exists, nothing is done.
    If not clear, and key is not found, the new password will be added.
    If not clear, and key is found, edit password in place.

    The passwords file contains both key-value pairs and key-dictionary
    pairs.
    """
    read_data = sync_read_file(file_path)
    file_pwds = yaml.safe_load(read_data)
    if clear:
        # clear
        if pname in file_pwds:
            del file_pwds[pname]
    else:
        # edit
        if private_key:
            file_pwds[pname] = {'private_key': private_key,
                                'public_key': public_key}
        else:
            if not pvalue:
                pvalue = None
            file_pwds[pname] = pvalue
    write_data = yaml.safe_dump(file_pwds, default_flow_style=False)
    sync_write_file(file_path, write_data)


def change_property(file_path, property_dict, clear=False):
    """change property with a file

    file_path:         path to property file
    property_dict:     dictionary of property names and values
    clear:             flag to remove property

    If clear, and property exists, remove it from the property file.
    If clear, and property doesn't exists, nothing is done.
    If not clear, and key is not found, the new property will be appended.
    If not clear, and key is found, edit property in place.
    """
    cloned_dict = copy.copy(property_dict)
    group_info = grp.getgrnam('kolla')
    if not os.path.exists(file_path):
        with open(file_path, 'a'):
            os.utime(file_path, None)
            os.chown(file_path, -1, group_info.gr_gid)

    new_contents = []
    read_data = sync_read_file(file_path)
    lines = read_data.split('\n')
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
            if split_key in cloned_dict:
                if clear:
                    # clear existing property
                    continue
                # edit existing property
                value = cloned_dict[split_key]
                line = _get_property_line(split_key, value)

                # clear out the key after we are done, all existing keys
                # will be appended at the end (or for clear, ignored)
                del cloned_dict[split_key]
        new_contents.append(line)
    if not clear:
        # add new properties to file
        for key, value in cloned_dict.items():
            line = _get_property_line(key, value)

            # when we are doing an append we want to avoid
            # blank lines before the new entry
            if new_contents[-1:][0] == '':
                del new_contents[-1]
            new_contents.append(line)

    # if the last line is blank, trim it off
    if new_contents[-1:][0] == '':
        del new_contents[-1]
    write_data = '\n'.join(new_contents) + '\n'
    sync_write_file(file_path, write_data)


def _get_property_line(key, value):
    if type(value) is str:
        line = '%s: "%s"' % (key, value)
    else:
        str_value = yaml.safe_dump(value).strip()
        if type(value) is bool:
            # yaml dump adds a newline and an ellipsis after
            # a boolean value. This needs to be stripped.
            str_value = str_value.replace('\n...', '')
        line = '%s: %s' % (key, str_value)
    return line


def sync_read_file(path, mode='r'):
    """synchronously read file

    return file data
    """
    lock = None
    try:
        if get_lock_enabled():
            lock = Lock(path, 'sync_read')
            locked = lock.wait_acquire()
            if not locked:
                raise Exception(
                    u._('unable to read file {path} '
                        'as it was locked.')
                    .format(path=path))
        with open(path, mode) as data_file:
            data = data_file.read()
    finally:
        if lock:
            lock.release()
    return safe_decode(data)


def sync_write_file(path, data, mode='w'):
    """synchronously write file"""
    ansible_lock = None
    lock = None
    try:
        if get_lock_enabled():
            ansible_lock = Lock(get_ansible_lock_path(), 'sync_write')
            locked = ansible_lock.wait_acquire()
            if not locked:
                raise Exception(
                    u._('unable to get ansible lock while writing to {path} '
                        'as it was locked.')
                    .format(path=path))

            lock = Lock(path, 'sync_write')
            locked = lock.wait_acquire()
            if not locked:
                raise Exception(
                    u._('unable to write file {path} '
                        'as it was locked.')
                    .format(path=path))
        with open(path, mode) as data_file:
            data_file.write(data)
    finally:
        if ansible_lock:
            ansible_lock.release()
        if lock:
            lock.release()


def safe_decode(obj_to_decode):
    """Convert bytes or strings to unicode string

    Converts strings, lists, or dictionaries to
    unicode.
    """
    if obj_to_decode is None:
        return None

    if isinstance(obj_to_decode, list):
        new_obj = []
        for text in obj_to_decode:
            text = safe_decode(text)
            new_obj.append(text)
    elif isinstance(obj_to_decode, dict):
        new_obj = {}
        for key, value in obj_to_decode.items():
            key = safe_decode(key)
            value = safe_decode(value)
            new_obj[key] = value
    else:
        new_obj = obj_to_decode
        if not isinstance(obj_to_decode, six.text_type):
            # object is not unicode
            new_obj = obj_to_decode.decode('utf-8')
    return new_obj


def is_string_true(string):
    """Return boolean True if string represents a true value (None is False)"""
    true_values = ['yes', 'true']
    if string is not None and string.lower() in true_values:
        return True
    else:
        return False


def convert_lists_to_string(tuples, parsed_args):
    """convert lists to strings

    Because of the way cliff processes strings for tables, if a list
    has non-ascii chars in it, they would display as unicode bytes
    (\u0414\u0435\u043a\u0430\u0442). By converting
    the list to string here, the proper non-ascii chars are displayed.

    This will only change the lists when the output is to a user visible
    medium. It cannot be changed if the display output is json, yaml, etc.
    """
    convert_types = ['table', 'csv', 'html', 'value']
    if parsed_args.formatter and parsed_args.formatter not in convert_types:
        # not table output, leave it as-is
        return tuples

    new_tuples = []
    for data_tuple in tuples:
        new_items = []
        items = list(data_tuple)
        for item in items:
            if isinstance(item, list):
                item = convert_list_to_string(item)
            new_items.append(item)
        data_tuple = tuple(new_items)
        new_tuples.append(data_tuple)
    return new_tuples


def convert_list_to_string(alist):
    return '[' + ','.join(alist) + ']'


def check_arg(param, param_name, expected_type, none_ok=False, empty_ok=False,
              display_param=True):
    if param is None:
        if none_ok:
            return
        # None arg
        raise MissingArgument(param_name)

    if ((isinstance(param, six.string_types) or
            isinstance(param, dict) or
            isinstance(param, list)) and
            not param and not empty_ok):
        # empty string, dict or list
        raise MissingArgument(param_name)

    # if expected type is None, skip the type checking
    if expected_type is None:
        return
    # normalize expected string types for py2 and py3
    if expected_type is str:
        expected_type = six.string_types

    if not isinstance(param, expected_type):
        # wrong type
        if display_param:
            raise InvalidArgument(u._('{name} ({param}) is not a {type}')
                                  .format(name=param_name, param=param,
                                          type=expected_type))
        else:
            raise InvalidArgument(u._('{name} is not a {type}')
                                  .format(name=param_name,
                                          type=expected_type))


class Lock(object):
    """Object which represents an exclusive resource lock

    flock usage is the default behavior but a separate pidfile mechanism
    is also available.  flock doesn't have the same orphaned lock issue
    that pidfile usage does.  both need to be tests on NFS.  if flock
    works then it seems better / less complicated for our needs.
    """

    def __init__(self, lockpath, owner='unknown owner', use_flock=True):
        self.lockpath = lockpath
        self.pid = str(os.getpid())
        self.fd = None
        self.owner = owner
        self.current_pid = -1
        self.current_owner = ''
        self.use_flock = use_flock

    def acquire(self):
            try:
                if self.use_flock:
                    return self._acquire_flock()
                else:
                    return self._acquire_pidfile()
            except Exception as e:
                if not os.path.exists(self.lockpath):
                    raise Exception('Lock file (%s) is missing'
                                    % self.lockpath)

                # it is ok to fail to acquire, we just return that we failed
                LOG.debug('Exception in acquire lock. '
                          'path: %s pid: %s owner: %s error: %s' %
                          (self.lockpath, self.pid, self.owner, str(e)))

    def _acquire_pidfile(self):
        if not self.is_owned_by_me():
            fd = os.open(self.lockpath, os.O_CREAT | os.O_EXCL | os.O_RDWR)
            with os.fdopen(fd, 'a') as f:
                f.write(self.pid + '\n' + self.owner)
            return self.is_owned_by_me()

    def _acquire_flock(self):
        self.fd = os.open(self.lockpath, os.O_RDWR)
        fcntl.flock(self.fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return True

    def wait_acquire(self, wait_duration=3, interval=0.1):
        wait_time = 0
        while (wait_time < wait_duration):
            if not self.acquire():
                time.sleep(interval)
                wait_time += interval
            else:
                return True
        return False

    def is_owned_by_me(self):
        """Returns True if we own the lock or False otherwise"""
        try:
            if self.use_flock:
                raise Exception(u._('Invalid use of is_owned_by_me while'
                                    'using flock'))

            if not os.path.exists(self.lockpath):
                # lock doesn't exist, just return
                return False
            fd = os.open(self.lockpath, os.O_RDONLY)
            with os.fdopen(fd, 'r') as f:
                contents = f.read(2048).strip().split('\n')
                if len(contents) > 0:
                    self.current_pid = contents[0]
                if len(contents) > 1:
                    self.current_owner = contents[1]

                if contents[0] == str(self.pid):
                    return True
                else:
                    return False
        except Exception as e:
            # it is ok to fail to acquire, we just return that we failed
            LOG.debug('Exception in is_owned_by_me lock check. '
                      'path: %s pid: %s owner: %s error: %s' %
                      (self.lockpath, self.pid, self.owner, str(e)))
        return False

    def release(self):
        try:
            if self.use_flock:
                self._release_flock()
            else:
                self._release_pidfile()
        except Exception:
            # this really shouldn't happen unless for some reason
            # two areas in the same process try to release the lock
            # at the same time and if that happens you want to see
            # an error about it
            LOG.error('Error releasing lock', exc_info=True)
            return False

    def _release_pidfile(self):
        if self.is_owned_by_me():
            os.remove(self.lockpath)
            return True

    def _release_flock(self):
        try:
            fcntl.flock(self.fd, fcntl.LOCK_UN)
        except Exception as e:
            LOG.debug('Exception while releasing lock: %s' % str(e))
        finally:
            os.close(self.fd)
        return True


class PidManager(object):
    @staticmethod
    def get_child_pids(pid, child_pids=[]):
        """get child pids of parent pid"""
        # This ps command will return child pids of parent pid, separated by
        # newlines.
        err_msg, output = run_cmd('ps --ppid %s -o pid=""' % pid,
                                  print_output=False)

        # err_msg is expected when pid has no children
        if not err_msg:
            output = output.strip()

            if '\n' in output:
                ps_pids = output.split('\n')
            else:
                ps_pids = [output]

            if ps_pids:
                child_pids.extend(ps_pids)

                # recurse through children to get all child pids
                for ps_pid in ps_pids:
                    PidManager.get_child_pids(ps_pid, child_pids)
        return child_pids
