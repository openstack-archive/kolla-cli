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

import os
import subprocess
import sys
import tarfile
import tempfile

from kollacli.ansible.inventory import Inventory
from kollacli.utils import get_admin_user
from kollacli.utils import get_kollacli_home
from kollacli.ansible import properties


def run_ansible_cmd(cmd, host):
    # sudo -u kolla ansible ol7-c4 -i
    #  /usr/share/kolla/kollacli/tools/json_generator.py -a "cmd"
    out = None
    user = get_admin_user()
    kollacli_home = get_kollacli_home()
    inv_path = os.path.join(kollacli_home, 'tools', 'json_generator.py')

    acmd = ('/usr/bin/sudo -u %s ansible %s -i %s -a "%s"'
            % (user, host, inv_path, cmd))

    try:
        (out, _) = subprocess.Popen(acmd, shell=True,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE).communicate()
    except Exception as e:
        print('%s\nCannot communicate with host: %s, skipping' % (e, host))

    if not out:
        print('Host %s is not accessible, skipping' % host)
    elif '>>' not in out:
        print('Ansible command: %s' % acmd)
        print('Host: %s. \nInvalid ansible return data: [%s]. skipping'
              % (host, out))
        out = None
    return out


def add_logdata_to_tar(logdata, tar, host, cname, cid):
    print('Adding container log %s:%s(%s)' % (host, cname, cid))
    fd, tmp_path = tempfile.mkstemp()
    os.close(fd)  # avoid fd leak
    with open(tmp_path, 'w') as tmpfile:
        tmpfile.write(logdata)
    tar.add(tmp_path, arcname='/%s/%s_%s.log' % (host, cname, cid))
    os.remove(tmp_path)


def get_containers(host):
    """return dict {id:name}"""
    cmd = '/bin/docker ps -a'
    out = run_ansible_cmd(cmd, host)
    if not out:
        return None
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

    containers = {}
    lines = out.split('\n')
    for line in lines:
        if container_prefix not in line:
            # skip non-kolla containers
            continue
        tokens = line.split()
        cid = tokens[0]
        image = tokens[1]
        name = image.split(container_prefix)[1]
        name = name.split(':')[0]
        containers[cid] = name
    return containers


def add_container_log(cid, cname, host, tar):
    cmd = '/bin/docker logs %s' % cid
    out = run_ansible_cmd(cmd, host)
    if out:
        out = out.split('>>', 1)[1]
        header = ('Host: %s, Container: %s, id: %s\n'
                  % (host, cname, cid))
        out = header + out
        add_logdata_to_tar(out, tar, host, cname, cid)


def add_logs_from_host(host, tar):
    containers = get_containers(host)
    if containers:
        for (cid, cname) in containers.items():
            add_container_log(cid, cname, host, tar)


def main():
    """collect docker logs from servers

    $ command is $ log_collector.py <all | host1[,host2,host3...]>
    """
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
    fd, tar_path = tempfile.mkstemp(prefix='kolla_docker_logs_',
                                    suffix='.tgz')
    os.close(fd)  # avoid fd leak

    with tarfile.open(tar_path, 'w:gz') as tar:
        for host in hosts:
            print('Getting docker logs from host: %s' % host)
            add_logs_from_host(host, tar)
    print('Log collection complete. Logs are at %s' % tar_path)

if __name__ == '__main__':
    main()
