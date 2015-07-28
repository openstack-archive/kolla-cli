===========
KollaClient
===========

The following steps can be used to build / run the kollaclient:

* virtualenv .venv
* . .venv/bin/activate
* pip install -r requirements.txt
* python setup.py install
* kollaclient

At that point you will be dropped into the kollaclient shell where
you can run commands like help or ? to see what commands are
available and any of the sub commands can be executed directly.

Alternately you can not use the shell and just execute commands
directly via >kollaclient host add, etc.

If you make changes to the i18n strings (denoted by methods like
_("message")) make sure to re-generate the i18n files with the
>python setup.py extract_messages command and check in the files
generated in openstack-kollaclient.

===============
Troubleshooting
===============

If you get an error about missing python.h install the python-dev
package via apt-get or yum or whatever mechanism is appropriate
for your platform.
