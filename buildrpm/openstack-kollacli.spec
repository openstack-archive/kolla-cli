# Copyright(c) 2015, Oracle.  All Rights Reserved.
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
# Package version (OpenStack release) may be not equal to module version
%define version_internal 0.1.0


Summary:        OpenStack Kolla CLI
Name:           openstack-kollacli
Version:        0.1
Release:        1%{?dist}
License:        Apache License, Version 2.0
Group:          Applications/System
Url:            https://launchpad.net/kolla
Source0:        http://ca-git.us.oracle.com/openstack-kollacli.git
Source1:        http://ca-git.us.oracle.com/openstack-kolla.git
BuildArch:      noarch


Requires: docker-engine >= 1.8.1
Requires: ansible >= 1.9.2
Requires: babel >= 1.3
Requires: python-babel >= 1.3
Requires: python-cliff-tablib >= 1.1
Requires: python-crypto >= 2.6.1
Requires: python-ecdsa >= 0.11
Requires: python-extras >= 0.0.3
Requires: python-fixtures >= 0.3.14
Requires: python-jsonpickle >= 0.9.2
Requires: python-mimeparse >= 0.1.4
Requires: python-oslo-i18n >= 1.3.0
Requires: python-paramiko >= 1.15.1
Requires: python-simplejson >= 3.2.0
Requires: python-six >= 1.9.0
Requires: python-tablib >= 0.10.0
Requires: python-testtools >= 1.1.0


%description
The Kolla Cli 


%prep
%setup -q -n openstack-kollacli-%{version}


%build
# generate temporary pkg-info file
PKGINFO_NAME=$(sed -n -e '/^name/ s/name\s=\s//p' setup.cfg)
PKGINFO_VERSION=$(sed -n -e '/^version/ s/version\s=\s//p' setup.cfg)
cat > PKG-INFO << __EOF__
Metadata-Version: 1.1
Name: $PKGINFO_NAME
Version: $PKGINFO_VERSION
__EOF__

#build package
%{__python} setup.py build --force


%install
%{__python} setup.py install --skip-build --root %{buildroot}

# install the OpenStack Kolla required files
install -p -D -m 640 %{SOURCE1}/ansible %{buildroot}/usr/share/kolla
install -p -D -m 640 %{SOURCE1}/etc/kolla %{buildroot}/etc/kolla

mkdir -p /usr/share/kolla/kollacli
mkdir -p /usr/share/kolla/kollacli/ansible

# remove unnecessary files
#rm -fr %{buildroot}%{python_sitelib}/muranoagent/tests/


%clean
rm -rf %{buildroot}


%files
%defattr(-,root,root)
%doc LICENSE
%{_bindir}/kollacli
%{python_sitelib}/kollacli-%{version_internal}-py%{pyver}.egg-info/*
%{python_sitelib}/kollacli/*


%changelog
* Tue Aug 25 2015 - Wiekus Beukes <wiekus.beukes@oracle.com>
- Initial release

