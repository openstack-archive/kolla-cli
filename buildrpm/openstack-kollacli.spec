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
%global package_version 0.1

# Kolla user name and group name (DO NOT CHANGE THESE!)
%global kolla_user      kolla
%global kolla_group     %{kolla_user}


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
Requires:       openstack-kolla-ansible     >= 0.1.0
Requires:       babel                       >= 2.0
Requires:       pexpect                     >= 2.3
Requires:       python-babel                >= 2.0
Requires:       python-cliff                >= 1.13.0
Requires:       python-cliff-tablib         >= 1.1
Requires:       python-jsonpickle           >= 0.9.2
Requires:       python-oslo-i18n            >= 2.5.0
Requires:       python-oslo-utils           !=2.6.0, >=2.4.0
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

# Create a kolla log directory
mkdir -m 0770 -p %{buildroot}/%{_var}/log/kolla

# Install the required OpenStack Kolla files
cp -r tools/* %{buildroot}/%{_datadir}/kolla/kollacli/tools
cp -r ansible/* %{buildroot}/%{_datadir}/kolla/kollacli/ansible

# Create an empty inventory file
touch %{buildroot}/%{_sysconfdir}/kolla/kollacli/ansible/inventory.json
chmod 0664 %{buildroot}/%{_sysconfdir}/kolla/kollacli/ansible/inventory.json

%clean
rm -rf %{buildroot}


%files
%defattr(-, %{kolla_user}, %{kolla_group})
%attr(-, root, root) %doc LICENSE
%attr(-, root, root) %{python_sitelib}
%attr(755, root, %{kolla_group}) %{_bindir}/kollacli
%attr(550, %{kolla_user}, %{kolla_group}) %dir %{_datadir}/kolla/kollacli/tools
%attr(500, %{kolla_user}, %{kolla_group}) %{_datadir}/kolla/kollacli/tools/passwd*
%attr(550, %{kolla_user}, %{kolla_group}) %{_datadir}/kolla/kollacli/tools/log_*
%attr(550, %{kolla_user}, %{kolla_group}) %{_datadir}/kolla/kollacli/ansible/*.yml
%attr(-, %{kolla_user}, %{kolla_group}) %config(noreplace) %{_sysconfdir}/kolla/kollacli
%attr(2770, %{kolla_user}, %{kolla_group}) %dir %{_var}/log/kolla

%post
setfacl -m d:g:%{kolla_group}:rw %{_var}/log/kolla

if ! test -f ~%{kolla_user}/.ssh/id_rsa
then
    runuser -m -s /bin/bash -c \
        "/usr/bin/ssh-keygen -q -t rsa -N '' -f ~%{kolla_user}/.ssh/id_rsa" \
        %{kolla_user}
fi

if ! test -f %{_sysconfdir}/kolla/kollacli/id_rsa.pub
then
    cp -p ~%{kolla_user}/.ssh/id_rsa.pub %{_sysconfdir}/kolla/kollacli/id_rsa.pub
    chmod 0440 %{_sysconfdir}/kolla/kollacli/id_rsa.pub
fi

/usr/bin/kollacli complete >/etc/bash_completion.d/kollacli 2>/dev/null

# Update the sudoers file
if ! grep -q 'kollacli/tools/passwd_editor' /etc/sudoers.d/%{kolla_user}
then
    sed -i \
        '/^Cmnd_Alias.*KOLLA_CMDS/ s:$:, %{_datadir}/kolla/kollacli/tools/passwd_editor.py:'\
        /etc/sudoers.d/%{kolla_user}
fi

# remove obsolete json_generator script
if test -f %{_datadir}/kolla/kollacli/tools/json_generator.py
then
    rm -f %{_datadir}/kolla/kollacli/tools/json_generator.py
fi

%postun
case "$*" in
    0)
        rm -f /etc/bash_completion.d/kollacli
    ;;
    *)
        ## Nothing for update
    ;;
esac


%changelog
* Fri Nov 06 2015 - Steve Noyes <steve.noyes@oracle.com>
- add python-oslo-utils requirement

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
