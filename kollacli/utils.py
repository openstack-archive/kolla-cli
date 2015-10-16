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
import os
import pexpect
import tempfile
import yaml

from lockfile import LockFile


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


def convert_to_unicode(the_string):
    """convert string to unicode.

    This is used to fixup extended ascii chars in strings. these chars cause
    errors in json pickle/unpickle.
    """
    uni_string = ''
    try:
        uni_string = unicode(the_string)
    except UnicodeDecodeError:
        uni_string = the_string.decode('utf-8')
    return uni_string


def run_cmd(cmd, print_output=True):
    """run a system command

    return:
    - err_flag: False=command succeeded
                True=command failed
    - output:   [List of strings]
                if error, provides error information
                if success, provides command output

    If the command is an ansible playbook command, record the
    output in an ansible log file.
    """
    pwd_prompt = '[sudo] password'
    log = logging.getLogger(__name__)
    err_flag = False
    output = []
    try:
        child = pexpect.spawn(cmd)
        sniff = child.read(len(pwd_prompt))
        if sniff == pwd_prompt:
            output.append(sniff + '\n')
            raise Exception(
                'Insufficient permissions to run command "%s"' % cmd)
        child.maxsize = 1
        child.timeout = 86400
        for line in child:
            outline = sniff + line.rstrip()
            sniff = ''
            output.append(outline)
            if print_output:
                log.info(outline)

    except Exception as e:
        err_flag = True
        output.append('%s' % e)
    finally:
        if child:
            child.close()
            if child.exitstatus != 0:
                err_flag = True
    return err_flag, output


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
    # lock is in /tmp to avoid permission issues
    lpath = os.path.join(tempfile.gettempdir(), os.path.basename(path))
    lock = LockFile(lpath)
    try:
        lock.acquire(True)
        with open(path, mode) as data_file:
            data = data_file.read()
    except Exception as e:
        raise e
    finally:
        lock.release()
    return data


def sync_write_file(path, data, mode='w'):
    """synchronously write file"""
    # lock is in /tmp to avoid permission issues
    lpath = os.path.join(tempfile.gettempdir(), os.path.basename(path))
    lock = LockFile(lpath)
    try:
        lock.acquire(True)
        with open(path, mode) as data_file:
            data_file.write(data)
    except Exception as e:
        raise e
    finally:
        lock.release()
