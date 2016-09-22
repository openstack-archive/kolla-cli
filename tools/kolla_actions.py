#!/usr/bin/env python
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
import getopt
import os
import signal
import subprocess
import sys
import yaml

from kollacli.common.utils import change_password


def _init_keys():
    cmd = 'kolla-genpwd'
    (_, err) = subprocess.Popen(cmd, shell=True,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE).communicate()
    if err:
        raise Exception('Error running %s: %s' % (cmd, err))


def _get_empty_keys(path):
    """get empty keys

    print string with keys that have empty pwd values
    """
    ok_empty = ['docker_registry_password']
    empty_keys = ''
    with open(path, 'r') as f:
        pwd_data = f.read()
    pwds = yaml.safe_load(pwd_data)
    comma = ''
    for pwd_key, pwd_val in pwds.items():
        is_empty = False
        if not pwd_val and pwd_key not in ok_empty:
            is_empty = True
        elif isinstance(pwd_val, dict):
            if not pwd_val.get('private_key', None):
                is_empty = True
            elif not pwd_val.get('public_key', None):
                is_empty = True
        if is_empty:
            empty_keys = ''.join([empty_keys, comma, pwd_key])
            comma = ','
    if empty_keys:
        print(empty_keys)


def _print_pwd_keys(path):
    keys_str = ''
    prefix = ''
    with open(path, 'r') as f:
        pwd_data = f.read()
    pwds = yaml.safe_load(pwd_data)
    for pwd_key in pwds.keys():
        keys_str = ''.join([keys_str, prefix, pwd_key])
        prefix = ','
    print(keys_str)


def _password_cmd(argv):
    """password command

    args for password command:
      -p path              # path to passwords.yaml
      -k key               # key of password
      -v value             # value of password (if not ssh keys)
      -r private key value # ssh private key
      -u public key value  # ssh public key
      -c                   # flag to clear the password
      -l                   # print to stdout a csv string of the existing keys
      -e                   # get keys of passwords with empty values
      -i                   # init empty keys and ssh keys
    """
    opts, _ = getopt.getopt(argv[2:], 'p:k:v:r:u:clei')
    path = ''
    pwd_key = ''
    pwd_value = ''
    pwd_ssh_private = ''
    pwd_ssh_public = ''
    clear_flag = False
    list_flag = False
    empty_flag = False
    init_flag = False
    for opt, arg in opts:
        if opt == '-p':
            path = arg
        elif opt == '-k':
            pwd_key = arg
        elif opt == '-v':
            pwd_value = arg
        elif opt == '-r':
            pwd_ssh_private = arg.replace('"', '')
        elif opt == '-u':
            pwd_ssh_public = arg.replace('"', '')
        elif opt == '-c':
            clear_flag = True
        elif opt == '-l':
            list_flag = True
        elif opt == '-e':
            empty_flag = True
        elif opt == '-i':
            init_flag = True
    if init_flag:
        # init empty keys
        _init_keys()
    elif list_flag:
        # print the password keys
        _print_pwd_keys(path)
    elif empty_flag:
        # get empty passwords
        _get_empty_keys(path)
    else:
        # edit/clear a password
        change_password(path, pwd_key, pvalue=pwd_value,
                        private_key=pwd_ssh_private,
                        public_key=pwd_ssh_public, clear=clear_flag)


def _job_cmd(argv):
    """jobs command

    args for job command
      -t       # terminate action
      -p pid   # process pid
    """
    opts, _ = getopt.getopt(argv[2:], 'tp:')
    pid = None
    term_flag = False
    for opt, arg in opts:
        if opt == '-p':
            pid = arg
        elif opt == '-t':
            term_flag = True

    if term_flag:
        try:
            os.kill(int(pid), signal.SIGKILL)
        except Exception as e:
            raise Exception('%s, pid %s' % (str(e), pid))


def main():
    """perform actions on behalf of kolla user

    sys.argv:
    sys.argv[1]   # command

    Supported commands:
    - password
    - job
    """
    if len(sys.argv) <= 1:
        raise Exception('Invalid number of parameters')

    command = sys.argv[1]
    if command == 'password':
        _password_cmd(sys.argv)
    elif command == 'job':
        _job_cmd(sys.argv)
    else:
        raise Exception('Invalid command %s' % command)

if __name__ == '__main__':
    main()
