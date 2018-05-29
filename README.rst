========
Kolla-CLI
========

The Kolla-CLI project provides the ability to more easily manage
Kolla-Ansible deployments. It provides both a CLI and a python
API that you can use to configure and deploy OpenStack using Kolla-Ansible.

Kolla-Ansible requires that hosts, groups, and services are specified
in an inventory file. With Kolla-CLI, you can add/remove hosts, change group
associations, etc from the CLI or API. Kolla-Ansible also maintains
passwords and various configuration variables in a variety of global, group
and host files. With Kolla-CLI, you can now view and change these from the
CLI/API.

Finally, Kolla-CLI provides commands to setup the SSH keys on hosts, run
deployments and perform upgrades.

Installing
==========

The following steps can be used to build / run the kolla-cli

* install ansible and docker
* virtualenv .venv
* . .venv/bin/activate
* pip install -r requirements.txt
* python setup.py install
* mkdir /usr/share/kolla-ansible
* cp -r kolla-ansible/ansible to /usr/share/kolla
* mkdir -p /etc/kolla/kolla-cli/ansible
* touch /etc/kolla/kolla-cli/ansible/inventory.json
* mkdir -p /usr/share/kolla-ansible/kolla-cli/tools
* mkdir /usr/share/kolla-ansible/kolla-cli/ansible
* touch /usr/share/kolla-ansible/kolla-cli/ansible.lock
* cp kolla-cli/tools /usr/share/kolla-ansible/kolla-cli/tools
* mkdir /usr/share/kolla-ansible/ansible/host_vars
* cp /etc/kolla/globals.yml /usr/share/kolla-ansible/ansible/group_vars/__GLOBAL__
* kolla-cli

At that point you will be dropped into the kollacli shell where
you can run commands like help or ? to see what commands are
available and any of the sub commands can be executed directly.

Alternately you can not use the shell and just execute commands
directly via >kollacli host add, etc.

If you make changes to the i18n strings (denoted by methods like
_("message")) make sure to re-generate the i18n files with the
>python setup.py extract_messages command and check in the files
generated in openstack-kollacli.


API
===

To use the API, import the ClientAPI into your module:

from kolla_cli.api.client import ClientApi

Then define a global:

CLIENT = ClientApi()

And then you can use that global to execute API commands, for example,
to add a host to the inventory:

CLIENT.host_add(['host_name'])

Troubleshooting
===============

If you get an error about missing python.h install the python-dev
package via apt-get or yum or whatever mechanism is appropriate
for your platform.
