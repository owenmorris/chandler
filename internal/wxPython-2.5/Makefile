
include ../Makefile.inc

# version info
VERSION=2.6.0.0
RELVER=$(VERSION)-7
WXMAJORVERSIONCOMPACT=26

SRC=$(INTERNAL)/wxPython-2.5
SWIG_OPTION=1
UNICODE_SUFFIX=u

# debug vs. release info
ifeq ($(DEBUG),1)
CONF_OPT=--enable-debug
DIST_OPT=--debug
FINAL=0
SUFFIX=d
PYTHON_SUFFIX=_d
else
CONF_OPT=--enable-optimized
DIST_OPT=
FINAL=1
SUFFIX=
PYTHON_SUFFIX=
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
CLEANITEMSALL= \
	$(SRC)/wxPython/docs/xml-raw/*.xml \
	$(SRC)/wxPython/src/$(OSTAG)/media.py \
	$(SRC)/wxPython/src/$(OSTAG)/media_wrap.cpp \
	$(SRC)/wxPython/contrib/gizmos/$(OSTAG)/gizmos.py \
	$(SRC)/wxPython/contrib/gizmos/$(OSTAG)/gizmos_wrap.cpp \
	$(SRC)/wxPython/contrib/glcanvas/$(OSTAG)/glcanvas.py \
	$(SRC)/wxPython/contrib/glcanvas/$(OSTAG)/glcanvas_wrap.cpp \
	$(SRC)/wxPython/contrib/stc/$(OSTAG)/stc.py \
	$(SRC)/wxPython/contrib/stc/$(OSTAG)/stc_wrap.cpp


# the working guts

BUILD=build_$(SNAP)

.PHONY: wxWidgets wxPython


ifeq ($(OS),Cygwin)

$(SRC)/include/wx/msw/setup.h:
	cd $(SRC); \
	sed -e "s/#define wxUSE_UNICODE 0/#define wxUSE_UNICODE 1/" include/wx/msw/setup0.h | \
	sed -e "s/#define wxUSE_DIALUP_MANAGER   1/#define wxUSE_DIALUP_MANAGER 0/" | \
	sed -e "s/#define wxUSE_DISPLAY       0/#define wxUSE_DISPLAY 1/" | \
	sed -e "s/#define wxUSE_RESOURCES   0/#define wxUSE_RESOURCES 1/" | \
	sed -e "s/#define wxUSE_POSTSCRIPT  0/#define wxUSE_POSTSCRIPT 1/"> include/wx/msw/setup.h

setup: $(SRC)/include/wx/msw/setup.h

wxWidgets: setup
	cd $(SRC); \
		export WXWIN=`cygpath -aw $(SRC)`; MAKEFLAGS=; \
		devenv.com build/msw/msw.sln /build $(Snap)
	mkdir -p $(PREFIX)/$(SITE)/wx
	install $(SRC)/lib/vc_dll/*$(WXMAJORVERSIONCOMPACT)$(UNICODE_SUFFIX)$(SUFFIX)*_vc.dll $(PREFIX)/$(SITE)/wx

wxPython:
	cd $(SRC)/wxPython; \
        export WXWIN=`cygpath -aw $(SRC)`; MAKEFLAGS=; \
	cp $(SRC)/wxPython/src/winxp.manifest $(BUILD_ROOT)/$(SNAP)/bin/chandler.exe.manifest; \
	cp $(SRC)/wxPython/src/winxp.manifest $(BUILD_ROOT)/$(SNAP)/bin/python$(PYTHON_SUFFIX).exe.manifest; \
	chmod a+x $(BUILD_ROOT)/$(SNAP)/bin/python$(PYTHON_SUFFIX).exe.manifest; \
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
	rm -rf $(CLEANITEMSALL)
	rm -rf $(SRC)/build/msw/vc_msw$(UNICODE_SUFFIX)$(SUFFIX)dll
	rm -rf $(SRC)/wxPython/contrib/build/animate/vc_msw$(UNICODE_SUFFIX)$(SUFFIX)dll
	rm -rf $(SRC)/wxPython/contrib/build/gizmos/vc_msw$(UNICODE_SUFFIX)$(SUFFIX)dll
	rm -rf $(SRC)/wxPython/contrib/build/stc/vc_msw$(UNICODE_SUFFIX)$(SUFFIX)dll
	rm -rf $(SRC)/wxPython/contrib/build/animate/wxPythonAnimate/Debug
	rm -rf $(SRC)/wxPython/contrib/build/animate/wxPythonAnimate/Release
	rm -rf $(SRC)/wxPython/$(BUILD)*
	rm -f $(SRC)/include/wx/msw/setup.h
	rm -f $(SRC)/lib/vc_dll/msw$(UNICODE_SUFFIX)$(SUFFIX)/setup.h
	cd $(SRC); MAKEFLAGS=; devenv.com build/msw/msw.sln /clean $(Snap)

cleanmanifest:
	cd $(BUILD_ROOT); \
	find $(MANIFEST) -name "*.pyc" | xargs rm -f; \
	find $(MANIFEST) -name "*.pyo" | xargs rm -f

else

ifeq ($(OS),Darwin)

$(SRC)/$(BUILD)/Makefile:
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
        MACOSX_DEPLOYMENT_TARGET=$(MACOSX_DEPLOYMENT_TARGET) $(PYTHON) setup.py \
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
	find $(SNAP)/$(SITE)/wx -name "*.pyc" | xargs rm -f; \
	find $(SNAP)/$(SITE)/wxPython -name "*.pyc" | xargs rm -f; \
	find $(SNAP)/$(SITE)/wx -name "*.pyo" | xargs rm -f; \
	find $(SNAP)/$(SITE)/wxPython -name "*.pyo" | xargs rm -f

else

$(SRC)/$(BUILD)/Makefile:
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
	find $(SNAP)/$(SITE)/wx -name "*.pyc" | xargs rm -f; \
	find $(SNAP)/$(SITE)/wxPython -name "*.pyc" | xargs rm -f; \
	find $(SNAP)/$(SITE)/wx -name "*.pyo" | xargs rm -f; \
	find $(SNAP)/$(SITE)/wxPython -name "*.pyo" | xargs rm -f

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
	rm -rf $(CLEANITEMSALL)
	rm -rf $(SRC)/wxPython/$(BUILD)*
	rm -rf $(SRC)/$(BUILD)

endif

build: wxWidgets wxPython

realclean: clean
	rm -f wxPython-debug-*.tar.gz* wxPython-release-*.tar.gz*

upload: wxPython-$(SNAP)-$(RELVER).tar.gz
	scp wxPython-$(SNAP)-$(RELVER).tar.gz $(UPLOAD)
	scp wxPython-$(SNAP)-$(RELVER).tar.gz.md5 $(UPLOAD)

snap: cleanmanifest
	cd $(BUILD_ROOT); \
	tar -cvzf $(SRC)/wxPython-$(SNAP)-$(RELVER).tar.gz $(MANIFEST)
	$(MD5) wxPython-$(SNAP)-$(RELVER).tar.gz > wxPython-$(SNAP)-$(RELVER).tar.gz.md5

install:
	cd $(BUILD_ROOT); \
	tar -cf - $(MANIFEST) | tar -C $(CHANDLERBIN) -xvf -
