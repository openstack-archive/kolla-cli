#!/usr/bin/env python
#
# Copyright 2018 OpenStack Foundation
# All Rights Reserved.
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
import os
import sys

from kolla_cli.common import utils

kolla_ansible_source_base = '../kolla-ansible'
kolla_ansible_home_target = utils.get_kolla_ansible_home()
kolla_ansible_etc_target = utils.get_kolla_etc()
ansible = 'ansible'
kolla = 'kolla'
kolla_cli = 'kolla-cli'
tools = 'tools'


def setup_ansible_etc():
    # if the kolla-cli directory for the inventory doesn't exist
    # already then make it. this will also create the directory the
    # globals and password file goes into
    cli_etc_dir = os.path.join(kolla_ansible_etc_target,
                               kolla_cli, ansible)
    if not os.path.exists(cli_etc_dir):
        make_cli_etc_dir_cmd = ('mkdir -p %s' % cli_etc_dir)
        _command_exec(make_cli_etc_dir_cmd)

    # Create the inventory file (if it doesn't already exist).
    # (The script will exit here if the user doesn't have sufficient privs.)
    inventory_file_path = os.path.join(cli_etc_dir, 'inventory.json')
    if not os.path.exists(inventory_file_path):
        touch_inventory_file_cmd = ('touch %s' % inventory_file_path)
        _command_exec(touch_inventory_file_cmd)

    # copy over all kolla ansible etc files
    kolla_ansible_etc_source = os.path.join(kolla_ansible_source_base,
                                            'etc', kolla)
    for etc_file in os.listdir(kolla_ansible_etc_source):
        if not os.path.exists(os.path.join(kolla_ansible_etc_target,
                                           etc_file)):
            copy_kolla_etc_files_cmd = (
                'cp -a {source_dir}/{filename} {target_dir}'.format(
                    source_dir=kolla_ansible_etc_source,
                    filename=etc_file,
                    target_dir=kolla_ansible_etc_target))
            _command_exec(copy_kolla_etc_files_cmd)

    # add ssh keys for cli
    key_path = os.path.join(os.getenv('HOME'), '.ssh', 'id_rsa')
    if not os.path.exists(key_path):
        # generate new ssh keys
        keygen_cmd = 'ssh-keygen -t rsa -N \'\' -f %s' % key_path
        _command_exec(keygen_cmd)
    # copy the public key to where kolla-cli expects it
    pub_key_path = os.path.join(os.getenv('HOME'), '.ssh', 'id_rsa.pub')
    cli_etc_path = os.path.join(kolla_ansible_etc_target, kolla_cli)
    copy_cmd = 'cp -p %s %s/' % (pub_key_path, cli_etc_path)
    _command_exec(copy_cmd)


def setup_ansible_home():
    # make cli home ansible directory
    cli_ansible_dir = os.path.join(kolla_ansible_home_target,
                                   kolla_cli, ansible)
    if not os.path.exists(cli_ansible_dir):
        make_cli_ansible_dir_cmd = ('mkdir -p %s' % cli_ansible_dir)
        _command_exec(make_cli_ansible_dir_cmd)

    # make cli home tools directory
    cli_tools_dir = os.path.join(kolla_ansible_home_target,
                                 kolla_cli, tools)
    if not os.path.exists(cli_tools_dir):
        make_cli_tools_dir_cmd = ('mkdir -p %s' % cli_tools_dir)
        _command_exec(make_cli_tools_dir_cmd)

    # move cli tools files to tools directory
    copy_cli_tools_files_cmd = ('cp -a %s %s' % ('./tools/*', cli_tools_dir))
    _command_exec(copy_cli_tools_files_cmd)

    # create cli ansible lock file
    lock_file_path = os.path.join(kolla_ansible_home_target,
                                  kolla_cli, 'ansible.lock')
    if not os.path.exists(lock_file_path):
        touch_ansible_lock_file_cmd = ('touch %s' % lock_file_path)
        _command_exec(touch_ansible_lock_file_cmd)

    # copy over all kolla ansible home files
    kolla_ansible_home_source = os.path.join(kolla_ansible_source_base,
                                             ansible)
    copy_kolla_home_files_cmd = ('cp -a %s %s' % (kolla_ansible_home_source,
                                                  kolla_ansible_home_target))
    _command_exec(copy_kolla_home_files_cmd)

    # create the host_vars directory if it doesn't exist already
    host_vars_path = os.path.join(kolla_ansible_home_target,
                                  ansible, 'host_vars')
    if not os.path.exists(host_vars_path):
        make_kolla_host_vars_dir_cmd = ('mkdir %s' % host_vars_path)
        _command_exec(make_kolla_host_vars_dir_cmd)

    # make link from etc globals to home globals
    target_etc_path = os.path.join(kolla_ansible_etc_target, 'globals.yml')
    target_home_link = os.path.join(kolla_ansible_home_target,
                                    ansible, 'group_vars', '__GLOBAL__')
    if not os.path.exists(target_home_link):
        link_globals_file_cmd = ('ln -s %s %s' % (target_etc_path,
                                                  target_home_link))
        _command_exec(link_globals_file_cmd)


def _command_exec(command):
    print('running - %s' % command)
    error, _ = utils.run_cmd(command)
    if error:
        print('error - %s' % error)
        sys.exit(1)


def main():
    """make sure kolla-ansible and cli files are in the right places"""

    if len(sys.argv) >= 2:
        global kolla_ansible_source_base
        kolla_ansible_source_base = sys.argv[1]

    setup_ansible_etc()
    setup_ansible_home()


if __name__ == '__main__':
    main()
