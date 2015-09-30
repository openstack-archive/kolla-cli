# Copyright(c) 2015, Oracle and/or its affiliates.  All Rights Reserved.
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

# This is an example file for defining the test configuration that can be
# used in the unit tests. The file should be named "test_config.json" and
# should be placed in the user"s home directory.
#
# The json.load() function is very finicky about syntax:
#
# - for any list object, the final member of the list must NOT have a
# comma after it. This will cause a "ValueError: Expecting property name..."
# exception.
# - double quotes are required for strings
#
# Example:
{
    "predeploy_cmds": [
        "setdeploy remote",
        "property set kolla_base_distro ol",
        "property set kolla_install_type openstack",
        "property set kolla_external_address 192.168.9.103",
        "property set kolla_internal_address 192.168.9.103",
        "property set docker_registry ca-qa-docker-reg.us.oracle.com:5000",
        "property set docker_namespace oracle",
        "property set docker_insecure_registry True",
        "property set network_interface enp0s3"
    ],
    "hosts": {
        "testhost1": {
            "uname": "root",
            "pwd": "password"
        },
        "testhost2": {
            "uname": "root",
            "pwd": "password"
        },
        "testhost3": {
            "uname": "root",
            "pwd": "password"
        }
    }
}
