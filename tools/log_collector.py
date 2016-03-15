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

import os
import subprocess
import sys
import tarfile
import tempfile
import traceback

from kollacli.common.inventory import Inventory
from kollacli.common import properties
from kollacli.common.utils import get_admin_user
from kollacli.common.utils import get_ansible_command
from kollacli.common.utils import safe_decode

tar_file_descr = None


def run_ansible_cmd(cmd, host):
    # sudo -u kolla ansible ol7-c4 -i inv_path -a "cmd"
    out = None
    user = get_admin_user()
    inv = Inventory.load()
    inv_path = inv.create_json_gen_file()

    ansible_verb = get_ansible_command()
    ansible_cmd = ('/usr/bin/sudo -u %s %s %s -i %s -a "%s"'
                   % (user, ansible_verb, host, inv_path, cmd))

    try:
        (out, err) = subprocess.Popen(ansible_cmd, shell=True,
                                      stdout=subprocess.PIPE,
                                      stderr=subprocess.PIPE).communicate()
    except Exception as e:
        print('%s\nCannot communicate with host: %s, skipping' % (e, host))
    finally:
        os.remove(inv_path)

    if not out:
        print('Host %s is not accessible: %s, skipping' % (host, err))
    else:
        out = safe_decode(out)
        if '>>' not in out:
            print('Ansible command: %s' % ansible_cmd)
            print('Host: %s. \nInvalid ansible return data: [%s]. skipping'
                  % (host, out))
            out = None
    return out


def add_logdata_to_tar(logdata, host, cname, cid):
    print('Adding container log %s:%s(%s)' % (host, cname, cid))
    archive_name = '/%s/%s_%s.log' % (host, cname, cid)
    tmp_path = None
    try:
        fd, tmp_path = tempfile.mkstemp()
        os.close(fd)  # avoid fd leak
        with open(tmp_path, 'w') as tmpfile:
            tmpfile.write(logdata)
        tar_file_descr.add(tmp_path, arcname=archive_name)
    except Exception:
        print('ERROR adding %s\n%s' % (archive_name, traceback.format_exc()))
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)


def get_containers(host):
    """return dict {id:name}"""
    cmd = 'docker ps -a'
    out = run_ansible_cmd(cmd, host)
    if not out:
        return None
    out = safe_decode(out)
    if 'NAMES' not in out:
        print('Host: %s. \nInvalid docker ps return data: [%s]. skipping'
              % (host, out))
        return None

    ansible_properties = properties.AnsibleProperties()
    base_distro = \
        ansible_properties.get_property('kolla_base_distro')
    install_type = \
        ansible_properties.get_property('kolla_install_type')
    # typically this prefix will be "ol-openstack-"
    container_prefix = base_distro + '-' + install_type + '-'

    # add ps output to tar
    add_logdata_to_tar(out, host, 'docker', 'ps')

    # process ps output
    containers = {}
    valid_found = False
    lines = out.split('\n')
    for line in lines:
        if container_prefix not in line:
            # skip non-kolla containers
            continue
        valid_found = True
        tokens = line.split()
        cid = tokens[0]
        image = tokens[1]
        name = image.split(container_prefix)[1]
        name = name.split(':')[0]
        containers[cid] = name
    if not valid_found:
        print('no containers with %s in image name found on %s'
              % (container_prefix, host))
    return containers


def add_container_log(cid, cname, host):
    cmd = 'docker logs %s' % cid
    out = run_ansible_cmd(cmd, host)
    if out:
        out = safe_decode(out)
        out = out.split('>>', 1)[1]
        header = ('Host: %s, Container: %s, id: %s\n'
                  % (host, cname, cid))
        out = header + out
        add_logdata_to_tar(out, host, cname, cid)


def add_logs_from_host(host):
    containers = get_containers(host)
    if containers:
        for (cid, cname) in containers.items():
            add_container_log(cid, cname, host)


def main():
    """collect docker logs from servers

    $ command is $ log_collector.py <all | host1[,host2,host3...]>
    """
    global tar_file_descr

    help_msg = 'Usage: log_collector.py <all | host1[,host2,host3...]>'
    hosts = []
    if len(sys.argv) == 2:
        if '-h' == sys.argv[1] or '--help' == sys.argv[1]:
            print(help_msg)
            sys.exit(0)
        elif 'all' == sys.argv[1]:
            # get logs from all hosts
            inventory = Inventory.load()
            hosts = inventory.get_hostnames()
        else:
            # get logs from specified hosts
            hostnames = sys.argv[1].split(',')
            for host in hostnames:
                if host not in hosts:
                    hosts.append(host)
    else:
        print(help_msg)
        sys.exit(1)

    # open tar file for storing logs
    fd, tar_path = tempfile.mkstemp(prefix='kolla_support_logs_',
                                    suffix='.tgz')
    os.close(fd)  # avoid fd leak

    with tarfile.open(tar_path, 'w:gz') as tar_file_descr:
        # gather dump output from kollacli
        print('Getting kollacli logs')
        # cliff prints log output to stderr
        (_, err) = subprocess.Popen('kollacli dump'.split(),
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE).communicate()
        err = safe_decode(err)
        if '/' in err:
            dump_path = '/' + err.strip().split('/', 1)[1]
            if os.path.isfile(dump_path):
                tar_file_descr.add(dump_path)
                os.remove(dump_path)
            else:
                print('ERROR: No kolla dump output file at %s' % dump_path)
        else:
            print('ERROR: No path found in dump command output: %s' % err)

        # gather logs from selected hosts
        for host in hosts:
            print('Getting docker logs from host: %s' % host)
            add_logs_from_host(host)
    print('Log collection complete. Logs are at %s' % tar_path)

if __name__ == '__main__':
    main()
