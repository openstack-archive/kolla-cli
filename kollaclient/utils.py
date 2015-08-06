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
import yaml


def get_kolla_home():
    return os.environ.get("KOLLA_HOME", "/opt/kolla/")


def get_kolla_etc():
    return os.environ.get("KOLLA_ETC", "/etc/kolla/")


def get_client_home():
    return os.environ.get("KOLLA_CLIENT_HOME", "/opt/kollaclient/")


def get_client_etc():
    return os.environ.get("KOLLA_CLIENT_ETC", "/etc/kolla/kollacli/")


def get_admin_user():
    return os.environ.get("KOLLA_ADMIN_USER", "kolla")


def get_pk_file():
    return os.environ.get("KOLLA_CLIENT_PKPATH",
                          "/etc/kolla/kollacli/etc/id_rsa")


def get_pk_password():
    # TODO(bmace) what to do here? pull from a file?
    return ""


def get_pk_bits():
    return 1024


def load_etc_yaml(fileName):
    contents = {}
    try:
        with open(get_client_etc() + fileName, 'r') as f:
            contents = yaml.load(f)
    except Exception:
        # TODO(bmace) if file doesn't exist on a load we don't
        # want to blow up, some better behavior here?
        pass
    return contents or {}


def save_etc_yaml(fileName, contents):
    with open(get_client_etc() + fileName, 'w') as f:
        f.write(yaml.dump(contents))


class Host(object):
    hostname = ''
    net_addr = ''
    zone = ''
    services = []

    def __init__(self, hostname, net_addr=''):
        self.hostname = hostname
        self.net_addr = net_addr


class Hosts(object):
    _hosts = {}

    def __init__(self):
        yml = load_etc_yaml('hosts.yml')
        for (hostname, info) in yml.items():
            host = Host(hostname)
            if 'NetworkAddress' in info:
                host.net_addr = info['NetworkAddress']
            if 'Zone' in info:
                host.zone = info['Zone']
            if 'Services' in info:
                service_list = info['Services']
                if service_list:
                    host.services = service_list.split(',')
            self._hosts[hostname] = host

    def get_all(self):
        return self._hosts.values()

    def get_host(self, hostname):
        host = None
        if hostname in self._hosts:
            host = self._hosts[hostname]
        return host

    def add_host(self, host):
        if host.hostname not in self._hosts:
            self._hosts[host.hostname] = host

    def remove_host(self, hostname):
        if hostname in self._hosts:
            del self._hosts[hostname]

    def save(self):
        """save hosts info"""
        info = {}
        for host in self._hosts.values():
            info[host.hostname] = {}
            info[host.hostname]['NetworkAddress'] = host.net_addr
            info[host.hostname]['Zone'] = host.zone
            info[host.hostname]['Services'] = []
            for service in host.services:
                info[host.hostname]['Services'].append(service)

        save_etc_yaml('hosts.yml', info)


class Zones(object):
    _zones = []

    def __init__(self):
        yml = load_etc_yaml('zones.yml')
        self._zones = yml.keys()

    def save(self):
        info = {}
        for zone in self._zones:
            info[zone] = ''
        save_etc_yaml('zones.yml', info)

    def add_zone(self, zone_name):
        if zone_name not in self._zones:
            self._zones.append(zone_name)

    def remove_zone(self, zone_name):
        if zone_name in self._zones:
            self._zones.remove(zone_name)

    def get_all(self):
        return self._zones
