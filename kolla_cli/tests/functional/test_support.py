# Copyright(c) 2016, Oracle and/or its affiliates.  All Rights Reserved.
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
from kolla_cli.tests.functional.common import KollaCliTest

import os
import shutil
import tarfile
import unittest

from kolla_cli.api.client import ClientApi
from kolla_cli.common.utils import get_tools_path
from kolla_cli.common.utils import safe_decode

LOGS_PREFIX = '/tmp/kolla_support_logs_'
CLIENT = ClientApi()

LOGDIR = '/tmp/utest_kolla_logs'


class TestFunctional(KollaCliTest):

    def test_log_collector(self):
        hostnames = ['test_host1']
        CLIENT.host_add(hostnames)

        zip_path = ''
        try:
            path = os.path.join(get_tools_path(),
                                'log_collector.py')

            # run the log_collector tool
            retval, msg = self.run_command('/usr/bin/python %s %s'
                                           % (path, 'all'))

            # no host, this should fail
            self.assertIn('error', msg.lower())
        except Exception as e:
            raise e
        finally:
            if zip_path and os.path.exists(zip_path):
                os.remove(zip_path)

    def test_log_collector_api(self):
        if os.path.exists(LOGDIR):
            shutil.rmtree(LOGDIR)
        os.mkdir(LOGDIR)

        hostnames = ['test_host1']
        CLIENT.host_add(hostnames)

        services = CLIENT.service_get_all()
        service_names = []
        for service in services:
            service_names.append(service.name)
        try:
            for hostname in hostnames:
                CLIENT.support_get_logs(service_names, safe_decode(hostname),
                                        LOGDIR)
                raise Exception('get_logs command succeeded without physical '
                                'hosts')
        except Exception as e:
            self.assertIn('UNREACHABLE', str(e),
                          'unexpected failure in get_logs: %s' % str(e))
        finally:
            if os.path.exists(LOGDIR):
                shutil.rmtree(LOGDIR)

    def test_dump(self):
        check_files = [
            'kolla/etc/kolla-cli/ansible/inventory.json',
            'kolla/share/ansible/site.yml',
        ]
        # dump success output is:
        # dump successful to /tmp/kollacli_dump_Umxu6d.tgz
        dump_path = None
        try:
            msg = self.run_cli_cmd('dump')
            self.assertIn('/', msg, 'path not found in dump output: %s' % msg)

            dump_path = '/' + msg.strip().split('/', 1)[1]
            is_file = os.path.isfile(dump_path)
            self.assertTrue(is_file,
                            'dump file not found at %s' % dump_path)
            with tarfile.open(dump_path, 'r') as tar:
                file_paths = tar.getnames()

            for check_file in check_files:
                self.assertIn(check_file, file_paths,
                              'dump: check file: %s, not in files:\n%s'
                              % (check_file, file_paths))
        except Exception as e:
            raise e
        finally:
            if dump_path and os.path.exists(dump_path):
                os.remove(dump_path)


if __name__ == '__main__':
    unittest.main()
