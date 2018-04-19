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
import logging
import os
import tarfile
import tempfile

from kolla_cli.api.exceptions import FailedOperation
from kolla_cli.common.inventory import Inventory
from kolla_cli.common.properties import AnsibleProperties
from kolla_cli.common.utils import get_kolla_ansible_home
from kolla_cli.common.utils import get_kolla_cli_etc
from kolla_cli.common.utils import run_cmd

LOG = logging.getLogger(__name__)


class HostLogs(object):

    def __init__(self, hostname, inventory, servicenames):
        self.hostname = hostname
        self.inventory = inventory
        self.servicenames = servicenames
        self.container_info = {}  # container_id: container_img_name
        self.filtered_servicenames = {}

    def load_container_info(self):
        """get the list of containers on the host"""
        hostname = self.hostname
        err_msg, output = \
            self.inventory.run_ansible_command('-a "docker ps -a"', hostname)
        if err_msg:
            msg = 'Error accessing host %s : %s %s' % (hostname, err_msg,
                                                       output)
            raise FailedOperation(msg)

        if not output:
            msg = ('Host %s is not accessible.' % hostname)
            raise FailedOperation(msg)
        else:
            if '>>' not in output:
                msg = ('Host: %s. Invalid ansible return data: [%s].'
                       % (hostname, output))
                raise FailedOperation(msg)

        if 'NAMES' not in output:
            msg = ('Host: %s. Invalid docker ps return data: [%s].'
                   % (hostname, output))
            raise FailedOperation(msg)

        ansible_properties = AnsibleProperties()
        base_distro = \
            ansible_properties.get_property_value('kolla_base_distro')
        install_type = \
            ansible_properties.get_property_value('kolla_install_type')
        # typically this prefix will be "ol-openstack-"
        container_prefix = base_distro + '-' + install_type + '-'

        # process ps output
        containers = {}

        # the ps output is after the '>>'
        output = output.split('>>', 1)[1]
        LOG.info('docker ps -a on host: %s:\n%s' % (hostname, output))

        lines = output.split('\n')
        for line in lines:
            tokens = line.split()
            if len(tokens) < 2:
                continue
            cid = tokens[0]
            image = tokens[1]
            if container_prefix not in image:
                # skip non-kolla containers
                continue
            name = image.split(container_prefix)[1]
            name = name.split(':')[0]
            containers[cid] = name
        self.container_info = containers

    def get_log(self, container_id):
        """read the container log"""
        hostname = self.hostname
        cmd = '-a "docker logs %s"' % container_id
        err_msg, output = self.inventory.run_ansible_command(cmd, hostname)
        if err_msg:
            msg = 'Error accessing host %s : %s ' % (hostname, err_msg)
            raise FailedOperation(msg)

        if not output:
            msg = ('Host %s is not accessible.' % hostname)
            raise FailedOperation(msg)
        if '>>' not in output:
            msg = ('Host: %s. Invalid ansible return data: [%s].'
                   % (hostname, output))
            raise FailedOperation(msg)

        # the log info is after the '>>'
        output = output.split('>>', 1)[1]
        return output

    def write_logs(self, dirname):
        """write out the log files for all containers"""
        for container_id, container_name in self.filtered_services.items():
            logdata = self.get_log(container_id)
            if logdata:
                logname = '%s_%s.log' % (container_name, container_id)
                self.write_logfile(dirname, logname, logdata)
            else:
                LOG.warn('No log data found for service %s on host %s'
                         % (container_name, self.hostname))

    def write_logfile(self, dirpath, logname, logdata):
        """write out one log file"""
        hostdir = os.path.join(dirpath, self.hostname)
        if not os.path.exists(hostdir):
            os.mkdir(hostdir)
        fpath = os.path.join(hostdir, logname)
        with open(fpath, 'w') as logfile:
            logfile.write(logdata)

    def filter_services(self):
        """filter services to only those of interest"""
        services_subset = {}
        for host_svcid, host_svcname in self.container_info.items():
            for servicename in self.servicenames:
                if (host_svcname == servicename or
                        host_svcname.startswith(servicename + '-')):
                    services_subset[host_svcid] = host_svcname
        self.filtered_services = services_subset


def get_logs(servicenames, hostname, dirname):
    inventory = Inventory.load()
    inventory.validate_hostnames([hostname])
    inventory.validate_servicenames(servicenames, client_filter=True)

    logs = HostLogs(hostname, inventory, servicenames)
    logs.load_container_info()
    logs.filter_services()
    logs.write_logs(dirname)


def dump(dirpath):
    """Dumps configuration data for debugging

    Dumps most files in /etc/kolla and /usr/share/kolla into a
    tar file so be given to support / development to help with
    debugging problems.
    """
    kolla_home = get_kolla_ansible_home()
    kolla_ansible = os.path.join(kolla_home, 'ansible')
    kollacli_etc = get_kolla_cli_etc().rstrip('/')
    ketc = 'kolla/etc/'
    kshare = 'kolla/share/'
    fd, dump_path = tempfile.mkstemp(dir=dirpath, prefix='kollacli_dump_',
                                     suffix='.tgz')
    os.close(fd)  # avoid fd leak
    with tarfile.open(dump_path, 'w:gz') as tar:
        # Can't blanket add kolla_home because the .ssh dir is
        # accessible by the kolla user only (not kolla group)
        tar.add(kolla_ansible,
                arcname=kshare + os.path.basename(kolla_ansible))

        # Can't blanket add kolla_etc because the passwords.yml
        # file is accessible by the kolla user only (not kolla group)
        tar.add(kollacli_etc,
                arcname=ketc + os.path.basename(kollacli_etc))

        # add output of various commands
        _add_cmd_info(tar)

    return dump_path


def _add_cmd_info(tar):
    # run all the kollacli list commands
    cmds = ['kolla-cli --version',
            'kolla-cli service listgroups',
            'kolla-cli service list',
            'kolla-cli group listservices',
            'kolla-cli group listhosts',
            'kolla-cli host list',
            'kolla-cli property list',
            'kolla-cli password list']

    # collect the json inventory output
    inventory = Inventory.load()
    inv_path = inventory.create_json_gen_file()
    cmds.append(inv_path)

    try:
        fd, path = tempfile.mkstemp(suffix='.tmp')
        os.close(fd)
        with open(path, 'w') as tmp_file:
            for cmd in cmds:
                err_msg, output = run_cmd(cmd, False)
                tmp_file.write('\n\n$ %s\n' % cmd)
                if err_msg:
                    tmp_file.write('Error message: %s\n' % err_msg)
                for line in output.split('\n'):
                    tmp_file.write(line + '\n')

        tar.add(path, arcname=os.path.join('kolla', 'cmds_output'))
    except Exception as e:
        raise e
    finally:
        if path:
            os.remove(path)
        inventory.remove_json_gen_file(inv_path)
    return
