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
import sys

from kollacli.common.utils import change_property
from kollacli.common.utils import sync_read_file


def _print_pwd_keys(path):
    pwd_keys = ''
    prefix = ''
    pwd_data = sync_read_file(path)
    for line in pwd_data.split('\n'):
        if line.startswith('#'):
            # skip commented lines
            continue
        if ':' in line:
            pwd_key = line.split(':')[0]
            pwd_keys = ''.join([pwd_keys, prefix, pwd_key])
            prefix = ','

    print(pwd_keys)


def _password_cmd(argv):
    """password command

    args for password command:
      -p path  # path to passwords.yaml
      -k key   # key of password
      -v value # value of password
      -c       # flag to clear the password
      -l       # print to stdout a csv string of the existing keys
    """
    opts, _ = getopt.getopt(argv[2:], 'p:k:v:cl')
    path = ''
    pwd_key = ''
    pwd_value = ''
    clear_flag = False
    list_flag = False
    for opt, arg in opts:
        if opt == '-p':
            path = arg
        elif opt == '-k':
            pwd_key = arg
        elif opt == '-v':
            pwd_value = arg
        elif opt == '-c':
            clear_flag = True
        elif opt == '-l':
            list_flag = True

    if list_flag:
        # print the password keys
        _print_pwd_keys(path)
    else:
        # edit a password
        property_dict = {}
        property_dict[pwd_key] = pwd_value
        change_property(path, property_dict, clear_flag)


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
