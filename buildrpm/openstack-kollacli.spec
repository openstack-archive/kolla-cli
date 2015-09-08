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
Release:        4%{?dist}
License:        Apache License, Version 2.0
Group:          Applications/System
Url:            https://launchpad.net/kolla
Source0:        %{name}-%{version}.tar
BuildArch:      noarch
BuildRequires:  python                      >= 2.7
BuildRequires:  python-setuptools           >= 0.9.8
BuildRequires:  python-pbr                  >= 1.3.0

Requires:       openstack-kolla-ansible     >= 0.1.0
Requires:       babel                       >= 0.9.6
Requires:       pexpect                     >= 2.3
Requires:       python-babel                >= 0.9.6
Requires:       python-cliff                >= 1.13.0
Requires:       python-cliff-tablib         >= 1.1
Requires:       python-jsonpickle           >= 0.9.2
Requires:       python-oslo-i18n            >= 1.3.0
Requires:       python-paramiko             >= 1.15.1
Requires:       python-pbr                  >= 1.3.0
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
mkdir -m 0755 -p %{buildroot}/%{_datadir}/kolla/kollacli/tools

# Install the required OpenStack Kolla files
cp -r tools/* %{buildroot}/%{_datadir}/kolla/kollacli/tools

# Create an empty inventory file
touch %{buildroot}/%{_sysconfdir}/kolla/kollacli/ansible/inventory.json
chmod 664 %{buildroot}/%{_sysconfdir}/kolla/kollacli/ansible/inventory.json


%clean
rm -rf %{buildroot}


%files
%defattr(-, %{kolla_user}, %{kolla_group})
%attr(-, root, root) %doc LICENSE
%attr(-, root, root) %{python_sitelib}
%attr(755, root, %{kolla_group}) %{_bindir}/kollacli
%attr(-, %{kolla_user}, %{kolla_group}) %{_datadir}/kolla/kollacli
%attr(-, %{kolla_user}, %{kolla_group}) %config(noreplace) %{_sysconfdir}/kolla/kollacli


%post
if ! test -f ~%{kolla_user}/.ssh/id_rsa
then
    sudo -u %{kolla_user} \
        /usr/bin/ssh-keygen -q -t rsa -N '' -f ~%{kolla_user}/.ssh/id_rsa
    cp -p ~%{kolla_user}/.ssh/id_rsa.pub %{_sysconfdir}/kolla/kollacli/id_rsa.pub
    chmod 0440 %{_sysconfdir}/kolla/kollacli/id_rsa.pub
fi


%changelog
* Tue Sep  8 2015 - Wiekus Beukes <wiekus.beukes@oracle.com>
- Added the creation of an empty inventory file to fix the permissions
- Changed %config to %config(noreplace)

* Thu Sep  3 2015 - Wiekus Beukes <wiekus.beukes@oracle.com>
- Fixed day of week
- Fixed all the post issues

* Wed Sep  2 2015 - Wiekus Beukes <wiekus.beukes@oracle.com>
- Initial release
