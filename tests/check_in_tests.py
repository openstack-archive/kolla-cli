#!/usr/bin/env python
# Copyright(c) 2015, Oracle and/or its affiliates.  All Rights Reserved.
#
#   Licensed under the Apache License, Version 2.0 (the "License"); you may
#   not use this file except in compliance with the License. You may obtain
#   a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#   WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#   License for the specific language governing permissions and limitations
#   under the License.
#
import os
import pexpect

DIR_TAG = 'openstack-kollacli'


def run_cmd(cmd):
        child = pexpect.spawn(cmd)
        child.maxsize = 1
        child.timeout = 86400
        for line in child:
            print(line.rstrip())
        child.close()


def get_tests_path():
    cwd = os.getcwd()
    if DIR_TAG not in cwd:
        raise('Must be in an %s directory' % DIR_TAG)
    tests_path = '/'
    tokens = cwd.split('/')
    for token in tokens:
        tests_path = os.path.join(tests_path, token)
        if token == DIR_TAG:
            break
    tests_path = os.path.join(tests_path, 'tests')
    return tests_path


def main():
    tests_path = get_tests_path()

    cmd = 'python -m unittest discover -p "*.*" -s %s' % tests_path
    run_cmd(cmd)

    cmd = 'tox -e pep8'
    run_cmd(cmd)


if __name__ == '__main__':
    main()
