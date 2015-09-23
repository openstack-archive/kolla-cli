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
import yaml


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
    log = logging.getLogger(__name__)
    err_flag = False
    output = []
    try:
        child = pexpect.spawn(cmd)
        child.maxsize = 1
        child.timeout = 86400
        for line in child:
            outline = line.rstrip()
            output.append(outline)
            if print_output:
                log.info(outline)
        child.close()
        if child.exitstatus != 0:
            err_flag = True
    except Exception as e:
        err_flag = True
        output.append('%s' % e)
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
        file_contents = []
        with open(file_path, 'r+') as property_file:
            new_line = '%s: "%s"\n' % (property_key, property_value)
            property_key_found = False
            for line in property_file:
                if line[0:len(property_key)] == property_key:
                    property_key_found = True
                    if clear:
                        # clear existing property
                        line = ''
                    else:
                        # edit existing property
                        line = new_line
                file_contents.append(line)
            if not property_key_found and not clear:
                # add new property to file
                file_contents.append(new_line)

            property_file.seek(0)
            property_file.truncate()

        with open(file_path, 'w') as property_file:
            for line in file_contents:
                property_file.write(line)
    except Exception as e:
        raise e
