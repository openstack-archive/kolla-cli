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
import os
import unittest

from kolla_cli.api import client
from kolla_cli.common.utils import get_kolla_etc
from kolla_cli.tests.functional.common import KollaCliTest

CLIENT = client.ClientApi()

PUBLIC_KEY = (
    'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQCqusDp5jpkbng3sRue8gZV6/PCQp9'
    'ogUd5/OZ3sh9VgdaigHoYUfXZElTZLlkL71tD9WZJr69PDwmG/nE4quba8rLcDY2wC0'
    'qjq+r06ExhlRu4ivy7OxT29s8FSe8Uht9Pz8ahnXxddLF55yTbC81XrSXDBFc6Nnogz'
    '+g6GgXVKtwTkm5g3K+qix5zVECu8zzawBR/s+v0dkDxKwSY8XOG6JZlMUndaDaikZZi'
    'qp8KAOJpajM77aCfDkY3VZGFBCJiEGLVDhFrtXuBI9I0YzX4j9pZZWpSzkM/FwlPjDR'
    'SW1C9MAAFLoEQTN4j1Z5hkDNXDsr49wJBi+jjQ0FPMMvfJktrznRuO2fUa9W2iilOrv'
    '1PyrknssmW1iYXiWJ5Bq8A9sKE1r7Nbdjhcjskp77X57tNjtarRUcj3FqGjC8pv+k92'
    '9Y+FvkXbjpBsHpdMFh8BlM+EnwnsjkiQpmjLv8bpeeQooLyQQmZn94zY73bbGrsjzXe'
    'OhOTDnKAS14hxCnBlEbudHB4erp/5Nj+A8UVAT0KXPM+mkDrum/dsvV0wnvBicAVt/a'
    'tmkwDKJqXDmj4elNe8/jTXSYHpTDo29xtcGpka9AtWarmnt8QkRuieD1xSXsEUQswjq'
    'aQD2ikitKt/hEyCmT+7fy4yYKK35kukUj5qV85A8O/hOYf5vFjtRw==')

PRIVATE_KEY = (
    '-----BEGIN RSA PRIVATE KEY-----\n'
    'MIIJKAIBAAKCAgEAqrrA6eY6ZG54N7EbnvIGVevzwkKfaIFHefzmd7IfVYHWooB6\n'
    'GFH12RJU2S5ZC+9bQ/VmSa+vTw8Jhv5xOKrm2vKy3A2NsAtKo6vq9OhMYZUbuIr8\n'
    'uzsU9vbPBUnvFIbfT8/GoZ18XXSxeeck2wvNV60lwwRXOjZ6IPoOhoF1SrcE5JuY\n'
    'Nyvqosec1RArvM82sAUf7Pr9HZA8SsEmPFzhuiWZTFJ3Wg2opGWYqqfCgDiaWozO\n'
    '+2gnw5GN1WRhQQiYhBi1Q4Ra7V7gSPSNGM1+I/aWWVqUs5DPxcJT4w0UltQvTAAB\n'
    'S6BEEzeI9WeYZAzVw7K+PcCQYvo40NBTzDL3yZLa850bjtn1GvVtoopTq79T8q5J\n'
    '7LJltYmF4lieQavAPbChNa+zW3Y4XI7JKe+1+e7TY7Wq0VHI9xahowvKb/pPdvWP\n'
    'hb5F246QbB6XTBYfAZTPhJ8J7I5IkKZoy7/G6XnkKKC8kEJmZ/eM2O922xq7I813\n'
    'joTkw5ygEteIcQpwZRG7nRweHq6f+TY/gPFFQE9ClzzPppA67pv3bL1dMJ7wYnAF\n'
    '69VedCYMSoYIHpcN80w9it/6Cfm8niAy3v9e0icSVEsvkzcV6eFjLggY1DQ9WBPN\n'
    'MR4LKGNDuxEWeZAQi+A6Ejclx1KKBhL/E4SNj3ev4/5glaMjzSIUpA4415o=\n'
    '-----END RSA PRIVATE KEY-----'
    )


class TestFunctional(KollaCliTest):

    def test_password_set_clear(self):
        # test list
        msg = self.run_cli_cmd('password list')
        key = 'database_password'
        value = '-'
        ok = self._password_value_exists(key, value, msg)
        self.assertTrue(ok, 'list failed. Password (%s/%s) not in output: %s'
                        % (key, value, msg))

        # test setting empty password
        self.run_cli_cmd('password set %s --insecure' % key)
        msg = self.run_cli_cmd('password list')
        ok = self._password_value_exists(key, '-', msg)
        self.assertTrue(ok, 'set empty password failed. Password ' +
                        '(%s/-) not in output: %s' %
                        (key, msg))

        # test setting None password
        CLIENT.password_set(key, None)
        msg = self.run_cli_cmd('password list')
        ok = self._password_value_exists(key, '-', msg)
        self.assertTrue(ok, 'set None password failed. Password ' +
                        '(%s/-) not in output: %s' %
                        (key, msg))

        # test clear
        key = 'database_password'
        value = '-'
        self.run_cli_cmd('password clear %s' % key)
        msg = self.run_cli_cmd('password list')
        ok = self._password_value_exists(key, value, msg)
        self.assertTrue(ok, 'clear password failed. Password ' +
                        '(%s/%s) not in output: %s' %
                        (key, value, msg))

        # test setting an ssh key
        key = 'nova_ssh_key'
        CLIENT.password_set_sshkey(key, PRIVATE_KEY, PUBLIC_KEY)
        keynames = CLIENT.password_get_names()
        self.assertIn(key, keynames, 'ssh key not in passwords')

        # test modify non-ssh password
        key = 'database_password'
        value = '-'
        self.run_cli_cmd('password set %s --insecure %s' % (key, value))
        msg = self.run_cli_cmd('password list')
        ok = self._password_value_exists(key, value, msg)
        self.assertTrue(ok, 'set modify password failed. Password ' +
                        '(%s/%s) not in output: %s' %
                        (key, value, msg))

        # test to make sure that saves / loads aren't doing something
        # bad to the password file size
        CLIENT.password_clear(key)
        # snapshot file size with key cleared
        password_file_path = os.path.join(get_kolla_etc(), 'passwords.yml')
        size_start = os.path.getsize(password_file_path)
        # set and clear password
        CLIENT.password_set(key, value)
        CLIENT.password_clear(key)
        size_end = os.path.getsize(password_file_path)
        self.assertEqual(size_start, size_end, 'password file size changed ' +
                         'during set/clear (%s/%s)' % (size_start, size_end))

        # make sure to end the test with the password init, as some other
        # non-password related tests require that all passwords in the file
        # be populated
        CLIENT.password_init()

    def _password_value_exists(self, key, value, cli_output):
        """Verify cli data against model data"""
        # check for any host in cli output that shouldn't be there
        cli_lines = cli_output.split('\n')
        for cli_line in cli_lines:
            if key in cli_line and value in cli_line:
                return True
        return False


if __name__ == '__main__':
    unittest.main()
