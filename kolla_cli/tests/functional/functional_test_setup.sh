#!/bin/bash
#
# Setup script for running kolla-cli functional tests.
#
# clean up files from last run
rm -f $KOLLA_ETC/kolla-cli/ansible/inventory.json
rm -f $KOLLA_HOME/ansible/group_vars/__GLOBAL__
rm -f $KOLLA_HOME/kolla-cli/ansible.lock
rm -f $KOLLA_ETC/passwords.yml

# setup the various files needed for the cli to run
mkdir -p $KOLLA_ETC/kolla-cli/ansible
touch $KOLLA_ETC/kolla-cli/ansible/inventory.json
mkdir -p $KOLLA_HOME/kolla-cli
touch $KOLLA_HOME/kolla-cli/ansible.lock

# If it's not there, clone the kolla-ansible repo to get its ansible directory
# and then copy it over
mkdir -p $KOLLA_HOME/git
if [ ! -d $KOLLA_HOME/ansible ]; then
    git clone https://github.com/openstack/kolla-ansible $KOLLA_HOME/git
    cp -rf $KOLLA_HOME/git/ansible $KOLLA_HOME/ansible/
fi

# setup needed kolla-ansible files
cp $KOLLA_HOME/git/etc/kolla/passwords.yml $KOLLA_ETC/passwords.yml
mkdir -p $KOLLA_HOME/ansible/host_vars
touch $KOLLA_HOME/ansible/group_vars/__GLOBAL__
