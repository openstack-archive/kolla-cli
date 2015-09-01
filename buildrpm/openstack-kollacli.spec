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

# Package version (OpenStack release) may be not equal to module version
%define kollacli_version_internal   0.1

# GIT repository base URL
%define git_base_url git://ca-git.us.oracle.com/


Summary:        OpenStack Kolla CLI
Name:           openstack-kollacli
Version:        0.1
Release:        1%{?dist}
License:        Apache License, Version 2.0
Group:          Applications/System
Url:            https://launchpad.net/kolla
Source0:        openstack-kollacli.tar.gz
Source1:        openstack-kolla.tar.gz
BuildArch:      noarch

Requires:       openstack-kolla-ansible >= 0.1
Requires:       babel                   >= 0.9.6
Requires:       pexpect                 >= 2.3
Requires:       python-babel            >= 0.9.6
Requires:       python-cliff            >= 1.13.0
Requires:       python-cliff-tablib     >= 1.1
Requires:       python-jsonpickle       >= 0.9.2
Requires:       python-oslo-i18n        >= 1.3.0
Requires:       python-paramiko         >= 1.15.1
Requires:       python-pbr              >= 1.3.0
Requires:       python-six              >= 1.9.0
Requires:       PyYAML                  >= 3.10


%description
The KollaCLI simplifies OpenStack Kolla deployments.


%prep
for _source in %{SOURCE0} %{SOURCE1}
do
  # If the SOURCE is not available we just automagically generate
  # it from the git repo for 
  #
  #   NOTE: THIS IS FOR TESTING ONLY as it always use master
  #
  if [[ ! -r ${_source} ]]
  then
    _name=$(basename ${_source} | sed 's/.tar.gz$//')
    _repo=%{git_base_url}${_name}'.git'
    git archive --format=tar --remote=${_repo} --prefix=${_name}/ --output=${RPM_SOURCE_DIR}/${_name}.tar master
    gzip ${RPM_SOURCE_DIR}/${_name}.tar
  fi

  rm -rf ${_name}
  gzip -dc ${_source} | tar -xvvf -
  if [ ${?} -ne 0 ]; then
    exit ${?}
  fi

  if [[ $(id -u) == 0 ]]
  then
    chown -R root.root ${_name}
    chmod -R a+rX,g-w,o-w ${_name}
  fi
done


%build
cd $(basename %{SOURCE0} | sed 's/.tar.gz$//')

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
%define kollacli_dir %(basename %{SOURCE0} | sed 's/.tar.gz$//')
%define kolla_dir ${RPM_BUILD_DIR}/$(basename %{SOURCE1} | sed 's/.tar.gz$//')

cd %{kollacli_dir}

# Install the package
%{__python} setup.py install --skip-build --root %{buildroot}

# Create the required directory structures
mkdir -p %{buildroot}/%{_sysconfdir}/kolla/kollacli/ansible
mkdir -p %{buildroot}/%{_datadir}/kolla/kollacli/tools

# Install the LICENSE file
install -p -D -m 444 LICENSE ${RPM_BUILD_DIR}

# Install the required OpenStack Kolla files
cp -r %{kolla_dir}/ansible %{buildroot}/%{_datadir}/kolla/
cp -r %{kolla_dir}/etc/kolla/* %{buildroot}/%{_sysconfdir}/kolla/
cp -r tools/* %{buildroot}/%{_datadir}/kolla/kollacli/tools


%clean
rm -rf %{buildroot}


%files
%defattr(-,root,root)
%doc LICENSE
%{_bindir}/kollacli
%{python_sitelib}/kollacli-%{kollacli_version_internal}-py%{pyver}.egg-info/*
%{python_sitelib}/kollacli/*
%{_datadir}/kolla/kollacli/*
%config %{_sysconfdir}/kolla/kollacli/*



# Package the Kolla dependent files
%package -n     openstack-kolla-ansible
Summary:        OpenStack Kolla Ansible playbooks and supporting files.
Version:        0.1
Release:        1%{?dist}
License:        Apache License, Version 2.0
Group:          Applications/System
Url:            https://launchpad.net/kolla

Requires:       ansible                 >= 1.9.2
Requires:       python-docker-py        >= 1.3.1


%description -n openstack-kolla-ansible
Ansible playbooks and support files to deploy Kolla in Docker containers.


%files -n openstack-kolla-ansible
%defattr(-,root,root)
%doc LICENSE
%{_datadir}/kolla/*
%config %{_sysconfdir}/kolla/*
%exclude %{_datadir}/kolla/kollacli
%exclude %{_sysconfdir}/kolla/kollacli


%changelog
* Thu Aug 27 2015 - Wiekus Beukes <wiekus.beukes@oracle.com>
- Split the Kolla Ansible files out into a seperate RPM

* Tue Aug 25 2015 - Wiekus Beukes <wiekus.beukes@oracle.com>
- Initial release

