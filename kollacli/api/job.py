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
from kollacli.common.utils import reraise


class Job(object):
    """Job"""
    def __init__(self, mesos_job):
        self._mesos_job = mesos_job

    def wait(self):
        """Wait for job to complete

        :return: 0 if job succeeded, 1 if job failed
        :rtype: int
        """
        try:
            return self._mesos_job.wait()
        except Exception as e:
            reraise(e)

    def get_status(self):
        """Get status of job

        :return: None: job is still running
                 0: job succeeded
                 1: job failed
                 2: job killed by user
        :rtype: int or None
        """
        try:
            return self._mesos_job.get_status()
        except Exception as e:
            reraise(e)

    def get_error_message(self):
        """Get error message

        :return: if job failed, this will return the error message.
        :rtype: string
        """
        try:
            return self._mesos_job.get_error_message()
        except Exception as e:
            reraise(e)

    def get_console_output(self):
        """Get the console output from the job

        :return: console output useful for debugging failed jobs.
        :rtype: string
        """
        try:
            return self._mesos_job.get_console_output()
        except Exception as e:
            reraise(e)

    def kill(self):
        """kill the job"""
        try:
            return self._mesos_job.kill()
        except Exception as e:
            reraise(e)
