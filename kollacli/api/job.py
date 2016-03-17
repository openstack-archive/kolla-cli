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


class Job(object):
    def __init__(self, ansible_job):
        self._ansible_job = ansible_job

    def wait(self):
        """wait for job to complete

        return status of job (see get_status() for status values)
        """
        return self._ansible_job.wait()

    def get_status(self):
        """get status of job

        Status:
        - None: still running
        - 0: complete/success
        - 1: complete/fail
        """
        return self._ansible_job.get_status()

    def get_error_message(self):
        """get error message

        if job failed, this will return a string with the error message.
        """
        return self._ansible_job.get_error_message()

    def get_console_output(self):
        """get command output

        get the console output from the job. Returns a string
        containing the console output of the job.
        """
        return self._ansible_job.get_command_output()
