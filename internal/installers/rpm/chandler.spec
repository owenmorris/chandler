Summary: Test Chandler
Name: Chandler
Version: 0.4
Release: 1
License: GPLv2
Group: Office
Vendor: Open Source Application Foundation
URL: http://www.osafoundation.org
BuildRoot: %{_builddir}/%{name}
Source0: chandler.tar.gz
Prefix: /usr/local
%description
Test Chandler RPM build
%install
cd $RPM_BUILD_ROOT
tar zxvf %{SOURCE0}
%clean
%files
/usr/local/Chandler
