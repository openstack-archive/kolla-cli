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


def get_client_home():
    return get_env("KOLLA_CLIENT_HOME", "/opt/kollaclient/")


def get_client_etc():
    return get_env("KOLLA_CLIENT_ETC", "/etc/kollaclient/etc/")


def get_admin_user():
    return get_env("KOLLA_ADMIN_USER", "kolla")


def get_pk_file():
    return get_env("KOLLA_CLIENT_PKPATH", "/opt/kollaclient/etc/id_rsa")


def get_pk_password():
    # TODO(bmace) what to do here? pull from a file?
    return ""


def get_pk_bits():
    return 1024


def load_etc_yaml(fileName):
    try:
        with open(get_client_etc() + fileName, 'r') as f:
            return yaml.load(f)
    except Exception:
        # TODO(bmace) if file doesn't exist on a load we don't
        # want to blow up, some better behavior here?
        return {}


def save_etc_yaml(fileName, contents):
    with open(get_client_etc() + fileName, 'w') as f:
        f.write(yaml.dump(contents))
