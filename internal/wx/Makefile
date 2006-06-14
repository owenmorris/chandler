#-*- Mode: Makefile; -*-
#
# internal/wx
#
# version info 
VERSION=2.6.2.0
VERSION_REVISION_INDEX=47
WX_VERSION_NODOT=26

RELVER=$(VERSION)-$(BRANCH_REV_PREFIX)$(VERSION_REVISION_INDEX)
SRC=$(INTERNAL)/wx
BUILD=build_$(SNAP)
TARBALL=wxPython-$(SNAP)-$(RELVER).tar.gz

include ../Makefile.inc

SWIG_OPTION=1
UNICODE_SUFFIX=u

# debug vs. release info
ifeq ($(DEBUG),1)
CONF_OPT=--enable-debug
DIST_OPT=--debug
FINAL=0
SUFFIX=d
PYTHON_SUFFIX=_d
W32_BUILD_TYPE='DLL Unicode Debug'
else
CONF_OPT=--enable-optimized
DIST_OPT=
FINAL=1
SUFFIX=
PYTHON_SUFFIX=
W32_BUILD_TYPE='DLL Unicode Release'
endif

# platform info
ifeq ($(OS),Cygwin)
OSTAG=msw
else
ifeq ($(OS),Darwin)
OSTAG=mac
else
OSTAG=gtk
endif
endif


# auto-generated items list (all platforms)
# this is called as "rm -f $(CLEANITEMSALL)" so be
# careful with your wildcards
CLEANITEMSALL= \
	$(SRC)/wxPython/build_options.py* \
	$(SRC)/wxPython/docs/xml-raw/*.xml \
	$(SRC)/wxPython/src/$(OSTAG)/* \
	$(SRC)/wxPython/wx/build/build_options.py \
	$(SRC)/wxPython/wx/build/config.py \
	$(SRC)/wxPython/contrib/activex/activex.py \
	$(SRC)/wxPython/include/wx/wxPython/swigver.h \
	$(SRC)/wxPython/contrib/activex/activex_wrap.py \
	$(SRC)/wxPython/contrib/animate/$(OSTAG)/* \
	$(SRC)/wxPython/contrib/gizmos/$(OSTAG)/* \
	$(SRC)/wxPython/contrib/glcanvas/$(OSTAG)/* \
	$(SRC)/wxPython/contrib/stc/$(OSTAG)/*


# the working guts

.PHONY: wxWidgets wxPython


ifeq ($(OS),Cygwin)

$(SRC)/include/wx/msw/setup.h: $(SRC)/include/wx/msw/setup0.h
	cd $(SRC); \
	sed -e "s/#define wxUSE_UNICODE 0/#define wxUSE_UNICODE 1/" include/wx/msw/setup0.h | \
	sed -e "s/#define wxUSE_DIALUP_MANAGER   1/#define wxUSE_DIALUP_MANAGER 0/" | \
	sed -e "s/#define wxUSE_DISPLAY       0/#define wxUSE_DISPLAY 1/" | \
	sed -e "s/#define wxUSE_RESOURCES   0/#define wxUSE_RESOURCES 1/" | \
	sed -e "s/#define wxUSE_NATIVE_COMPOSITING   0/#define wxUSE_NATIVE_COMPOSITING 1/" | \
	sed -e "s/#define wxUSE_POSTSCRIPT  0/#define wxUSE_POSTSCRIPT 1/"> include/wx/msw/setup.h

setup: $(SRC)/include/wx/msw/setup.h

buildDLLs: setup
	cd $(SRC); \
		export WXWIN=`cygpath -aw $(SRC)`; MAKEFLAGS=; \
		devenv.com build/msw/wx_osaf.sln /build $(W32_BUILD_TYPE)

installDLLs:
	mkdir -p $(PREFIX)/$(SITE)/wx
	install $(SRC)/lib/vc_dll/*$(WX_VERSION_NODOT)$(UNICODE_SUFFIX)$(SUFFIX)*_vc*.dll $(PREFIX)/$(SITE)/wx
	if [ -f "$(SRC)/lib/vc_dll/wxbase$(WX_VERSION_NODOT)$(UNICODE_SUFFIX)$(SUFFIX)_vc_custom.bsc" ]; \
	then \
		install $(SRC)/lib/vc_dll/*.bsc $(PREFIX)/$(SITE)/wx; \
	fi

wxWidgets: buildDLLs

wxWidgets: installDLLs

wxPython:
	cd $(SRC)/wxPython; \
        export WXWIN=`cygpath -aw $(SRC)`; MAKEFLAGS=; \
	cp $(SRC)/wxPython/src/winxp.manifest $(BUILD_ROOT)/$(SNAP)/bin/chandler.exe.manifest; \
	cp $(SRC)/wxPython/src/winxp.manifest $(BUILD_ROOT)/$(SNAP)/bin/python$(PYTHON_SUFFIX).exe.manifest; \
	chmod a+x $(BUILD_ROOT)/$(SNAP)/bin/python$(PYTHON_SUFFIX).exe.manifest; \
	chmod a+x $(BUILD_ROOT)/$(SNAP)/bin/chandler.exe.manifest; \
	$(PYTHON) setup.py BUILD_BASE=$(BUILD) \
                UNICODE=1 BUILD_ACTIVEX=0 BUILD_GLCANVAS=0 \
                USE_SWIG=$(SWIG_OPTION) \
                SWIG=`cygpath -aw $(SWIG)` \
                INSTALL_MULTIVERSION=0 \
                MONOLITHIC=0 \
                build $(DIST_OPT) \
                install \
                FINAL=$(FINAL) HYBRID=0

MANIFEST=$(SNAP)/$(SITE)/wx $(SNAP)/bin/chandler.exe.manifest $(SNAP)/bin/python$(PYTHON_SUFFIX).exe.manifest

clean:
	rm -f $(CHANDLERBIN)/$(SNAP)/$(TARBALL).inst
	rm -f $(CLEANITEMSALL)
	find $(SRC)/wxPython/wx -maxdepth 1 -type f -print | xargs rm -f
	rm -rf $(SRC)/build/msw/vc_msw$(UNICODE_SUFFIX)$(SUFFIX)dll
	rm -rf $(SRC)/contrib/build/animate/vc_msw$(UNICODE_SUFFIX)$(SUFFIX)dll
	rm -rf $(SRC)/contrib/build/animate/wxPythonAnimate/Debug
	rm -rf $(SRC)/contrib/build/animate/wxPythonAnimate/Release
	rm -rf $(SRC)/contrib/build/gizmos/vc_msw$(UNICODE_SUFFIX)$(SUFFIX)dll
	rm -rf $(SRC)/contrib/build/gizmos/wxPythonGizmos/Debug
	rm -rf $(SRC)/contrib/build/gizmos/wxPythonGizmos/Release
	rm -rf $(SRC)/contrib/build/stc/vc_msw$(UNICODE_SUFFIX)$(SUFFIX)dll
	rm -rf $(SRC)/contrib/build/stc/wxPythonStc/Debug
	rm -rf $(SRC)/contrib/build/stc/wxPythonStc/Release
	rm -rf $(SRC)/wxPython/$(BUILD)*
	rm -rf $(SRC)/build/msw/vc_msw$(UNICODE_SUFFIX)dll
	rm -rf $(SRC)/contrib/build/gizmos/vc_msw$(UNICODE_SUFFIX)dll
	rm -rf $(SRC)/contrib/build/stc/vc_msw$(UNICODE_SUFFIX)dll
	rm -rf $(SRC)/contrib/build/animate/vc_msw$(UNICODE_SUFFIX)dll
	rm -f $(SRC)/include/wx/msw/setup.h
	rm -f $(SRC)/lib/vc_dll/*.bsc
	rm -f $(SRC)/lib/vc_dll/msw$(UNICODE_SUFFIX)$(SUFFIX)/setup.h
	cd $(SRC); MAKEFLAGS=; devenv.com build/msw/wx_osaf.sln /clean $(W32_BUILD_TYPE)

cleanmanifest:
	cd $(BUILD_ROOT); \
	find $(SNAP)/$(SITE)/wx -name ".svn" | xargs rm -rf; \
	find $(SNAP)/$(SITE)/wxPython -name ".svn" | xargs rm -rf; \
	find $(MANIFEST) -name "*.pyc" | xargs rm -f; \
	find $(MANIFEST) -name "*.pyo" | xargs rm -f

else

ifeq ($(OS),Darwin)

$(SRC)/$(BUILD)/Makefile: $(SRC)/Makefile.in
	cd $(SRC); mkdir -p $(BUILD); cd $(BUILD); \
	MACOSX_DEPLOYMENT_TARGET=$(MACOSX_DEPLOYMENT_TARGET) ../configure --prefix=$(PREFIX) $(CONF_OPT) \
		--enable-monolithic \
		--enable-unicode \
		--enable-geometry \
		--enable-sound \
		--enable-display \
		--with-sdl \
		--with-libpng \
		--with-libtiff=builtin \
		--with-mac

wxPython:
	cd $(SRC)/wxPython; \
        MACOSX_DEPLOYMENT_TARGET=$(MACOSX_DEPLOYMENT_TARGET) \
        DYLD_FRAMEWORK_PATH=$(PREFIX)/Library/Frameworks \
	$(PYTHON) setup.py \
                UNICODE=1 BUILD_OGL=0 BUILD_GLCANVAS=0 \
                USE_SWIG=$(SWIG_OPTION) \
                SWIG=$(SWIG) \
                INSTALL_MULTIVERSION=0 \
                BUILD_BASE=$(BUILD) \
                WX_CONFIG=$(PREFIX)/bin/wx-config \
                build $(DIST_OPT) install FINAL=$(FINAL)

MANIFEST=$(SNAP)/$(SITE)/wx \
         $(SNAP)/$(SITE)/wxPython \
	 $(SNAP)/lib/libwx* \
	 $(SNAP)/share/locale

cleanmanifest:
	cd $(BUILD_ROOT); \
	find $(SNAP)/$(SITE)/wx -name ".svn" | xargs rm -rf; \
	find $(SNAP)/$(SITE)/wxPython -name ".svn" | xargs rm -rf; \
	find $(SNAP)/$(SITE)/wx -name "*.pyc" | xargs rm -f; \
	find $(SNAP)/$(SITE)/wxPython -name "*.pyc" | xargs rm -f; \
	find $(SNAP)/$(SITE)/wx -name "*.pyo" | xargs rm -f; \
	find $(SNAP)/$(SITE)/wxPython -name "*.pyo" | xargs rm -f
	rm -f $(CHANDLERBIN)/$(SNAP)/$(TARBALL).inst

else

$(SRC)/$(BUILD)/Makefile: $(SRC)/Makefile.in
	cd $(SRC); mkdir -p $(BUILD); cd $(BUILD); \
	../configure --prefix=$(PREFIX) $(CONF_OPT) \
		--enable-monolithic \
		--enable-unicode \
		--enable-geometry \
		--enable-sound \
		--disable-display \
		--with-sdl \
		--with-libpng \
		--with-libtiff=builtin \
		--with-gtk=2

wxPython:
	cd $(SRC)/wxPython; \
        export LD_LIBRARY_PATH=$(PREFIX)/lib; \
        $(PYTHON) setup.py \
                UNICODE=1 BUILD_OGL=0 BUILD_GLCANVAS=0 \
                USE_SWIG=$(SWIG_OPTION) \
                SWIG=$(SWIG) \
                INSTALL_MULTIVERSION=0 \
                BUILD_BASE=$(BUILD) \
                WX_CONFIG=$(PREFIX)/bin/wx-config \
                WXPORT=gtk2 \
                build $(DIST_OPT) install FINAL=$(FINAL)

MANIFEST=$(SNAP)/$(SITE)/wx \
         $(SNAP)/$(SITE)/wxPython \
	 $(SNAP)/lib/libwx* \
	 $(SNAP)/share/locale

cleanmanifest:
	cd $(BUILD_ROOT); \
	find $(SNAP)/$(SITE)/wx -name ".svn" | xargs rm -rf; \
	find $(SNAP)/$(SITE)/wxPython -name ".svn" | xargs rm -rf; \
	find $(SNAP)/$(SITE)/wx -name "*.pyc" | xargs rm -f; \
	find $(SNAP)/$(SITE)/wxPython -name "*.pyc" | xargs rm -f; \
	find $(SNAP)/$(SITE)/wx -name "*.pyo" | xargs rm -f; \
	find $(SNAP)/$(SITE)/wxPython -name "*.pyo" | xargs rm -f
	rm -f $(CHANDLERBIN)/$(SNAP)/$(TARBALL).inst

endif

wxWidgets: $(SRC)/$(BUILD)/Makefile
	$(MAKE) -C $(SRC)/$(BUILD)
	$(MAKE) -C $(SRC)/$(BUILD)/contrib/src/gizmos
	$(MAKE) -C $(SRC)/$(BUILD)/contrib/src/animate
	$(MAKE) -C $(SRC)/$(BUILD)/contrib/src/stc
	$(MAKE) -C $(SRC)/$(BUILD) install
	$(MAKE) -C $(SRC)/$(BUILD)/contrib/src/gizmos install
	$(MAKE) -C $(SRC)/$(BUILD)/contrib/src/animate install
	$(MAKE) -C $(SRC)/$(BUILD)/contrib/src/stc install

clean:
	rm -f $(CLEANITEMSALL)
	find $(SRC)/wxPython/wx -maxdepth 1 -type f -print | xargs rm -f
	rm -rf $(SRC)/wxPython/$(BUILD)*
	rm -rf $(SRC)/$(BUILD)
	rm -f $(CHANDLERBIN)/$(SNAP)/$(TARBALL).inst

endif

build: wxWidgets wxPython

realclean: clean
	rm -f wxPython-debug-*.tar.gz* wxPython-release-*.tar.gz*

snap: cleanmanifest strip
	cd $(BUILD_ROOT); \
    tar -cvzf $(SRC)/$(TARBALL) $(MANIFEST)

install:
	cp $(TARBALL) $(CHANDLERARCHIVES)
