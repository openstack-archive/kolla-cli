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
import shutil
import sys
import tarfile
import tempfile
import traceback

from kolla_cli.api.client import ClientApi

tar_file_descr = None

CLIENT = ClientApi()

LOGDIR = '/tmp/container_logs'


def get_logs_from_host(host):
    try:
        service_names = []
        services = CLIENT.service_get_all()
        for service in services:
            service_names.append(service.name)

        print('Adding container logs from host: %s' % host)
        CLIENT.support_get_logs(service_names, host, LOGDIR)
    except Exception as e:
        print('Error getting logs on host: %s: %s' % (host, str(e)))


def dump_kolla_info():
    print('Getting kolla client logs')
    dump_path = None
    try:
        dump_path = CLIENT.support_dump('/tmp')
        tar_file_descr.add(dump_path)
    except Exception:
        print('ERROR: running dump command %s' % traceback.format_exc())
    finally:
        if dump_path and os.path.exists(dump_path):
            os.remove(dump_path)


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
            hosts = []
            host_objs = CLIENT.host_get_all()
            for host_obj in host_objs:
                hosts.append(host_obj.name)
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
        # clear out old logs
        if os.path.exists(LOGDIR):
            shutil.rmtree(LOGDIR)
        os.mkdir(LOGDIR)

        # gather logs from selected hosts
        try:
            for host in hosts:
                get_logs_from_host(host)

            # tar up all the container logs
            tar_file_descr.add(LOGDIR, arcname='container_logs')
        finally:
            # remove uncompressed logs
            if os.path.exists(LOGDIR):
                shutil.rmtree(LOGDIR)

        # gather dump output from kolla-cli
        dump_kolla_info()

    print('Log collection complete. Logs are at %s' % tar_path)


if __name__ == '__main__':
    main()
