Version: 0.4
Release: 1
Summary: Test Chandler
Name: Chandler
License: GPLv2
Group: Office
Vendor: Open Source Applications Foundation
URL: http://www.osafoundation.org
BuildRoot: %{_builddir}/%{name}
Source0: chandler.tar.gz
Prefix: /usr/local
AutoReqProv: no
%description
Test Chandler RPM build
%install
cd $RPM_BUILD_ROOT
tar zxvf %{SOURCE0}
#%post
#if [ "$1" = 1 ];
#then
# add post-install script here
#fi
%preun
if [ "$1" = 0 ];
then
find $RPM_INSTALL_PREFIX/Chandler -type f -name '*.pyc' -exec rm -f {} \;
fi
#note that the __repository__ directory and any lock file are not removed
rm -f $RPM_INSTALL_PREFIX/Chandler/randpool.dat
rm -f $RPM_INSTALL_PREFIX/Chandler/cacert.pem
rm -f $RPM_INSTALL_PREFIX/Chandler/chandler.log
%files
/usr/local/Chandler
