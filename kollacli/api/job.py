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
    """Job"""
    def __init__(self, ansible_job):
        self._ansible_job = ansible_job

    def wait(self):
        # type: () -> int
        """Wait for job to complete

        :return: 0 if job succeeded, 1 if job failed
        :rtype: int
        """
        return self._ansible_job.wait()

    def get_status(self):
        # type: () -> int
        """Get status of job

        :return: None: job is still running
                 0: job succeeded
                 1: job failed
                 2: job killed by user
        :rtype: int or None
        """
        return self._ansible_job.get_status()

    def get_error_message(self):
        # type: () -> str
        """Get error message

        :return: if job failed, this will return the error message.
        :rtype: string
        """
        return self._ansible_job.get_error_message()

    def get_console_output(self):
        # type: () -> str
        """Get the console output from the job

        :return: console output useful for debugging failed jobs.
        :rtype: string
        """
        return self._ansible_job.get_command_output()

    def kill(self):
        """kill the job"""
        self._ansible_job.kill()
