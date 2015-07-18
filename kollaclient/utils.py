import os
import yaml


def get_env(var, default):
    value = os.environ.get(var, None)
    if value:
        return value
    return default


def get_kolla_home():
    return get_env("KOLLA_HOME", "/opt/kolla")


def get_kolla_etc():
    return get_env("KOLLA_ETC", "/etc")


def get_client_etc():
    return get_env("KOLLA_CLIENT_ETC", "/etc/kollaclient/")


def get_client_home():
    return get_env("KOLLA_CLIENT_HOME", "/opt/kollaclient/")


def read_etc_yaml(fileName):
    with open(get_client_etc() + fileName, 'r') as f:
        return yaml.load(f)


def save_etc_yaml(fileName, contents):
    with open(get_client_etc() + fileName, 'w') as f:
        f.write(yaml.dump(contents))
