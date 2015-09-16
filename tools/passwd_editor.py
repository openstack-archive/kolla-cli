#!/usr/bin/env python
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
import getopt
import sys

from kollacli import utils


def _print_pwd_keys(path):
    pwd_keys = ''
    prefix = ''
    with open(path, 'r') as pwd_file:
        for line in pwd_file:
            if line.startswith('#'):
                # skip commented lines
                continue
            if ':' in line:
                pwd_key = line.split(':')[0]
                pwd_keys = pwd_keys + prefix + pwd_key
                prefix = ','

    print(pwd_keys)


def main():
    """edit password in passwords.yml file

    sys.argv:
    -p path  # path to passwords.yaml
    -k key   # key of password
    -v value # value of password
    -c       # flag to clear the password
    -l       # print to stdout a csv string of the existing keys
    """
    opts, _ = getopt.getopt(sys.argv[1:], 'p:k:v:cl')
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
        utils.change_property(path, pwd_key, pwd_value, clear_flag)


if __name__ == '__main__':
    main()
