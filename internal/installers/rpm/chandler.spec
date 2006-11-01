#
# Remember to update the makeinstaller.sh script if you update
# the Version or Release info - it sadly requires that info
# so it can copy the generated .rpm file properly
# 
#
# This spec file is very lightweight as most of the work
# has already been done by the build process.
# The rpm -ba call is made *after* the source files
# are placed into the RPM_BUILD_ROOT directory (that's
# why you don't see an install section below or even
# a Source/Source0 entry)
#

Version: %{_dv}
Release: %{_dr}
Summary: Chandler - an Open Source Personal Information Manager
Name: Chandler
License: Apache2
Group: Office
Vendor: Open Source Applications Foundation
URL: http://www.osafoundation.org
BuildRoot: %{_builddir}/OSAF
Prefix: /usr/local
AutoReqProv: no
#Source0: chandler.tar.gz
%description
Chandler is a next-generation Personal Information Manager (PIM), 
integrating calendar, email, contact management, task management, 
notes, and instant messaging functions. 
#%install
#cd $RPM_BUILD_ROOT
#tar zxvf %{SOURCE0}
#%clean
#if [ -d "$RPM_BUILD_ROOT/usr/local/chandler-%{_dv}" ]; then
#rm -rf $RPM_BUILD_ROOT
#fi
#%post
#if [ "$1" = 1 ]; then
# add post-install script here
#fi
#%preun
#if [ "$1" = 0 ]; then
#find $RPM_INSTALL_PREFIX/chandler -type f -name '*.pyc' -exec rm -f {} \;
#find $RPM_INSTALL_PREFIX/chandler -type f -name '*.pyo' -exec rm -f {} \;
#fi
%files
%defattr(-,root,root)
/usr/local/chandler-%{_dv}
