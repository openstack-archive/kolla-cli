=========
Kolla-CLI
=========

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

The installation process below assumes that the kolla-ansible repository
exists at the same level as the kolla-cli repository. This is made clear
in the cli_setup.py script which makes a relative '../' reference to
the kolla-ansible repository. If your kolla-ansible directory is somewhere
else then that location can be passed as an argument to the cli_setup.py
script. The location on the system where the kolla-cli expects the
kolla-ansible files to be and installs them to can be tweaked by setting
the KOLLA_HOME and KOLLA_ETC environment variables before running the
cli_setup.py script, and while running the kolla-cli command itself. The
default value for KOLLA_HOME is /usr/share/kolla-ansible and the default
value for KOLLA_ETC is /etc/kolla.

The following steps can be used to build / run the kolla-cli

* install ansible and docker
* virtualenv .venv
* . .venv/bin/activate
* pip install -r requirements.txt
* python setup.py install
* python ./cli_setup.py
* kolla-cli

At that point you will be dropped into the kollacli shell where
you can run commands like help or ? to see what commands are
available and any of the sub commands can be executed directly.

Alternately you can not use the shell and just execute commands
directly via kollacli host add, etc.

If you make changes to the i18n strings (denoted by methods like
_("message")) make sure to re-generate the i18n files with the
``python setup.py extract_messages`` command and check in the
files generated in openstack-kollacli.


API
===

To use the API, import the ClientAPI into your module:

from kolla_cli.api.client import ClientApi

Then define a global:

CLIENT = ClientApi()

And then you can use that global to execute API commands, for example,
to add a host to the inventory:

CLIENT.host_add(['host_name'])

Generating Documentation
========================

We use `Sphinx <https://pypi.python.org/pypi/Sphinx>`_ to maintain the
documentation. You can install Sphinx using pip.

::

    $ pip install -U Sphinx

In addition to Sphinx you will also need the following requirements
(not covered by `requirements.txt`)::

    $ pip install openstackdocstheme reno 'reno[sphinx]'

The source code of the documentation are under *doc*, you can generate the
html files using the following command. If the generation succeeds,a
*build/html* dir will be created under *doc*.

::

    $ cd doc
    $ make html

Now you can serve the documentation at http://localhost:8080 as a simple
website.

::

    $ cd build/html
    $ python -m SimpleHTTPServer 8080

Getting Involved
================

Need a feature? Find a bug? Let us know! Contributions are much
appreciated and should follow the standard `Gerrit
workflow <https://docs.openstack.org/infra/manual/developers.html>`__.

-  We communicate using the #openstack-kolla irc channel.
-  File bugs, blueprints, track releases, etc on
   `Launchpad <https://launchpad.net/kolla-cli>`__.
-  Attend weekly
   `meetings <https://wiki.openstack.org/wiki/Meetings/Kolla>`__.
-  Contribute `code <https://opendev.org/openstack/kolla-cli>`__.

Contributors
============

Check out who is `contributing
code <https://www.stackalytics.com/?module=kolla-group&metric=commits>`__ and
`contributing
reviews <https://www.stackalytics.com/?module=kolla-group&metric=marks>`__.

Troubleshooting
===============

If you get an error about missing python.h install the python-dev
package via apt-get or yum or whatever mechanism is appropriate
for your platform.
