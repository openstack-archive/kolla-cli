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

# Python major version.
%{expand: %%define pyver %(python -c 'import sys;print(sys.version[0:3])')}

# Package version
%global package_version 3.0.1

# Kolla user name and group name (DO NOT CHANGE THESE!)
%global kolla_user      kolla
%global kolla_group     %{kolla_user}

# kolla ansible plugin related vars
%global plugin_dir      %{_datadir}/ansible/plugins/callback
%global plugin_name     kolla_callback

Summary:        OpenStack Kolla CLI
Name:           openstack-kollacli
Version:        %{package_version}
Release:        10%{?dist}
License:        Apache License, Version 2.0
Group:          Applications/System
Url:            https://launchpad.net/kolla
Source0:        %{name}-%{version}.tar
BuildArch:      noarch
BuildRequires:  python                      >= 2.7
BuildRequires:  python-setuptools           >= 0.9.8
BuildRequires:  python-pbr                  >= 1.3.0
Requires:       openstack-kolla-ansible-plugin >= 3.0.0
Requires:       babel                       >= 2.0
Requires:       python-babel                >= 2.0
Requires:       python-cliff                >= 1.13.0
Requires:       python-cliff-tablib         >= 1.1
Requires:       python-jsonpickle           >= 0.9.2
Requires:       python-oslo-i18n            >= 2.5.0
Requires:       python-paramiko             >= 1.15.1
Requires:       python-pbr                  >= 1.6.0
Requires:       python-six                  >= 1.9.0
Requires:       PyYAML                      >= 3.10

Requires:       /usr/bin/ssh-keygen

%description
The KollaCLI simplifies OpenStack Kolla deployments.

%prep
%setup -q -n %{name}-%{version}

%build
# Generate a temporary pkg-info file to make pbr happy
PKGINFO_NAME=$(sed -n -e '/^name/ s/name\s=\s//p' setup.cfg)
PKGINFO_VERSION=$(sed -n -e '/^version/ s/version\s=\s//p' setup.cfg)
cat >PKG-INFO <<__EOF__
Metadata-Version: 1.1
Name: ${PKGINFO_NAME}
Version: ${PKGINFO_VERSION}
__EOF__

# Build the package
%{__python} setup.py build


%install
# Install the package
%{__python} setup.py install --skip-build --root %{buildroot}

# Create the required directory structures
mkdir -m 0755 -p %{buildroot}/%{_sysconfdir}/kolla/kollacli
mkdir -m 0775 -p %{buildroot}/%{_sysconfdir}/kolla/kollacli/ansible
mkdir -m 0750 -p %{buildroot}/%{_datadir}/kolla/kollacli/tools
mkdir -m 0750 -p %{buildroot}/%{_datadir}/kolla/kollacli/ansible
mkdir -m 0755 -p %{buildroot}/%{_datadir}/kolla/ansible

# Create a kolla log directory
mkdir -m 0770 -p %{buildroot}/%{_var}/log/kolla

# Install the required OpenStack Kolla files
cp -r tools/* %{buildroot}/%{_datadir}/kolla/kollacli/tools
cp -r ansible/* %{buildroot}/%{_datadir}/kolla/kollacli/ansible
cp -r openstack-kolla-data/ansible.cfg %{buildroot}/%{_datadir}/kolla/.ansible.cfg
cp -r openstack-kolla-data/ansible/prechecks_preinstall.yml %{buildroot}/%{_datadir}/kolla/ansible/prechecks_preinstall.yml

# Create an empty inventory file
touch %{buildroot}/%{_sysconfdir}/kolla/kollacli/ansible/inventory.json
chmod 0664 %{buildroot}/%{_sysconfdir}/kolla/kollacli/ansible/inventory.json

# copy over plugin
mkdir -p %{buildroot}/%{plugin_dir}
cp -r ansible_plugins/%{plugin_name}.py %{buildroot}/%{plugin_dir}/

%clean
rm -rf %{buildroot}


%files
%defattr(-, %{kolla_user}, %{kolla_group})
%attr(-, root, root) %doc LICENSE
%attr(-, root, root) %{python_sitelib}
%attr(755, root, %{kolla_group}) %{_bindir}/kollacli
%attr(550, %{kolla_user}, %{kolla_group}) %dir %{_datadir}/kolla/kollacli/tools
%attr(500, %{kolla_user}, %{kolla_group}) %{_datadir}/kolla/kollacli/tools/kolla_actions*
%attr(550, %{kolla_user}, %{kolla_group}) %{_datadir}/kolla/kollacli/tools/log_*
%attr(550, %{kolla_user}, %{kolla_group}) %{_datadir}/kolla/kollacli/ansible/*.yml
%attr(-, %{kolla_user}, %{kolla_group}) %config(noreplace) %{_sysconfdir}/kolla/kollacli
%attr(2770, %{kolla_user}, %{kolla_group}) %dir %{_var}/log/kolla
%attr(644, %{kolla_user}, %{kolla_group}) %{_datadir}/kolla/ansible/prechecks_preinstall.yml

%pre
case "$*" in
    0)
        #
        # Install package
        #
        inst_type="install"
        ;;
    *)
        #
        # Update package
        #
        inst_type="update"
        ;;
esac

if [[ "${inst_type}" == "update" ]]
then
    rm -rf %{python_sitelib}/kollacli-*egg-info 2> /dev/null
fi

%post
setfacl -m d:g:%{kolla_group}:rw %{_var}/log/kolla

if ! test -f %{_datadir}/kolla/kollacli/ansible.lock
then
    touch %{_datadir}/kolla/kollacli/ansible.lock
    chown %{kolla_user}:%{kolla_group} %{_datadir}/kolla/kollacli/ansible.lock
    chmod 0660 %{_datadir}/kolla/kollacli/ansible.lock
fi

if ! test -f ~%{kolla_user}/.ssh/id_rsa
then
    runuser -m -s /bin/bash -c \
        "/usr/bin/ssh-keygen -q -t rsa -N '' -f ~%{kolla_user}/.ssh/id_rsa" \
        %{kolla_user}
fi

# always copy the key over, in case it was re-created in kolla/.ssh
cp -p ~%{kolla_user}/.ssh/id_rsa.pub %{_sysconfdir}/kolla/kollacli/id_rsa.pub
chmod 0440 %{_sysconfdir}/kolla/kollacli/id_rsa.pub

/usr/bin/kollacli complete >%{_sysconfdir}/bash_completion.d/kollacli 2>/dev/null

# Update the sudoers file
if ! grep -q 'kollacli/tools/kolla_actions' %{_sysconfdir}/sudoers.d/%{kolla_user}
then
    sed -i \
        '/^Cmnd_Alias.*KOLLA_CMDS/ s:$:, %{_datadir}/kolla/kollacli/tools/kolla_actions.py:'\
        %{_sysconfdir}/sudoers.d/%{kolla_user}
fi
# remove obsolete password editor from sudoers file
sed -i \
    '/^Cmnd_Alias.*KOLLA_CMDS/ s:, %{_datadir}/kolla/kollacli/tools/passwd_editor.py::'\
     %{_sysconfdir}/sudoers.d/%{kolla_user}

# remove obsolete json_generator script
if test -f %{_datadir}/kolla/kollacli/tools/json_generator.py
then
    rm -f %{_datadir}/kolla/kollacli/tools/json_generator.py
fi

# remove obsolete password editor script
if test -f %{_datadir}/kolla/kollacli/tools/passwd_editor.py.py
then
    rm -f %{_datadir}/kolla/kollacli/tools/passwd_editor.py.py
fi


%postun
case "$*" in
    0)
        rm -f %{_sysconfdir}/bash_completion.d/kollacli
        rm -rf %{_datadir}/kolla/kollacli
    ;;
    *)
        ## Nothing for update
    ;;
esac


# kolla ansible plugin rpm specific work
%package -n openstack-kolla-ansible-plugin

Summary:        OpenStack Kolla Ansible Plugin
Version:        %{package_version}
License:        GNU General Public License, Version 3
Group:          Applications/System
# The plugin needs ansible 2.1 which is in the
# requirement for openstack-kolla-ansible
Requires:       openstack-kolla-ansible     >= 3.0.0
Requires:       openstack-kolla-ansible     < 4.0.0

%description -n openstack-kolla-ansible-plugin
This ansible plugin supplies playbook activity to the
openstack-kollacli client.

%files -n openstack-kolla-ansible-plugin
%defattr(-, %{kolla_user}, %{kolla_group})
%attr(-, root, root) %doc ansible_plugins/LICENSE
%attr(755, %{kolla_user}, %{kolla_group}) %{plugin_dir}/*
%attr(644, %{kolla_user}, %{kolla_group}) %{_datadir}/kolla/.ansible.cfg

%changelog
* Mon Sep 12 2016 - Steve Noyes <steve.noyes@oracle.com>
- move ansible.cfg from kolla to kollacli rpm

* Fri May 27 2016 - Steve Noyes <steve.noyes@oracle.com>
- always copy rsa_id.pub key to /etc/kolla/kollacli

* Mon May 23 2016 - Steve Noyes <steve.noyes@oracle.com>
- Removed all ansible cfg references, will be handled by kolla buildspec

* Tue May 17 2016 - James McCarthy <james.m.mccarthy@oracle.com>
- Updated pipeling setting in line with bug 23282017

* Thu May 5 2016 - James McCarthy <james.m.mccarthy@oracle.com>
- Updated plugin_dir to be in line with paths in default file

* Fri Apr 29 2016 - Wiekus Beukes <wiekus.beukes@oracle.com>
- Updated the kolla-ansible requirement to 3.0.0

* Wed Apr 13 2016 - Steve Noyes <steve.noyes@oracle.com>
- add kolla-ansible-plugin subpackage
- suppress warning on egg removal
- remove etc and usr/share refs

* Thu Apr 07 2016 - Borne Mace <borne.mace@oracle.com>
- added ansible.lock file to coordinate ansible synchronization

* Thu Apr 07 2016 - Steve Noyes <steve.noyes@oracle.com>
- rename passwd_editor.py to kolla_actions.py

* Tue Apr 05 2016 - Steve Noyes <steve.noyes@oracle.com>
- remove obsolete pexpect requirement

* Tue Feb 23 2016 - Borne Mace <borne.mace@oracle.com>
- added clean up of old egg-info directories during update

* Tue Feb 23 2016 - Steve Noyes <steve.noyes@oracle.com>
- disable retry_files_enabled in ansible.cfg

* Thu Feb 11 2016 - Steve Noyes <steve.noyes@oracle.com>
- disallow pexpect 3.3 (sudo issue)
- remove obsolete oslo-utils reference

* Mon Oct 26 2015 - Steve Noyes <steve.noyes@oracle.com>
- Remove obsolete json_generator

* Fri Oct  2 2015 - Wiekus Beukes <wiekus.beukes@oracle.com>
- Allow user to precreate the ssh keys

* Thu Oct 01 2015 - Steve Noyes <steve.noyes@oracle.com>
- replace sudo command with runuser

* Fri Sep 25 2015 - Steve Noyes <steve.noyes@oracle.com>
- added sticky bits and acl to simplify logging permissions

* Thu Sep 24 2015 - Steve Noyes <steve.noyes@oracle.com>
- Added kolla log dir under /var/log/

* Thu Sep 17 2015 - Borne Mace <borne.mace@oracle.com>
- Added the ansible directory under /usr/share/kolla/kollacli
- Added code to copy the kollacli specific playbooks into that directory

* Wed Sep 16 2015 - Wiekus Beukes <wiekus.beukes@oracle.com>
- Added the bash completion setup
- Added code to augment the kolla sudo file for the password mgmt piece

* Tue Sep  8 2015 - Wiekus Beukes <wiekus.beukes@oracle.com>
- Updated dependencies
- Added the creation of an empty inventory file to fix the permissions
- Changed %config to %config(noreplace)

* Thu Sep  3 2015 - Wiekus Beukes <wiekus.beukes@oracle.com>
- Fixed day of week
- Fixed all the post issues

* Wed Sep  2 2015 - Wiekus Beukes <wiekus.beukes@oracle.com>
- Initial release
