
VERSION=2.6.16
RELVER=$(VERSION)-4
LIBXML2=$(BUILD_ROOT)/persistence/libxml2
SRC=$(LIBXML2)/libxml2-$(VERSION)

include $(BUILD_ROOT)/Makefile.inc

ifeq ($(OS),Darwin)
WP=$(PREFIX)/$(FRAMEWORK)
else
WP=$(PREFIX)
endif

ifeq ($(OS),Cygwin)

ifeq ($(DEBUG),1)
CONF_DBG=debug=yes
else
CONF_DBG=
endif

BUILD=win32/$(SNAP)

$(SRC)/$(BUILD)/config.msvc: apply
	mkdir -p $(SRC)/$(BUILD)
	cp -p win32/winSetup.py.in $(SRC)/python
	cd $(SRC)/win32; \
	cscript //E:JScript configure.js prefix=$(SNAP) $(CONF_DBG) \
                            python=yes iconv=no iso8859x=yes 

compile: $(SRC)/$(BUILD)/config.msvc
	cd $(SRC)/win32; MAKEFLAGS=; \
	nmake -nologo -f Makefile.msvc BUILD_VERSION=$(SNAP) all install

py:
	cd $(SRC)/python; \
	$(PYTHON) winSetup.py build --build-base=build_$(SNAP) $(DIST_OPT) \
                              install --force

build: expand compile py

clean:
	cd $(SRC)/win32; rm -rf $(SNAP)
	cd $(SRC)/python; rm -rf build_$(SNAP)

snap: 
	cd $(BUILD_ROOT); \
        tar -cvzf $(LIBXML2)/libxml2-$(SNAP)-$(RELVER).tar.gz \
                  $(SNAP)/$(SITE)/*libxml2*; \
	$(MD5) $(LIBXML2)/libxml2-$(SNAP)-$(RELVER).tar.gz > $(LIBXML2)/libxml2-$(SNAP)-$(RELVER).tar.gz.md5

else

ifeq ($(DEBUG),1)
CONF_DBG=--enable-debug
else
CONF_DBG=
endif

BUILD=build_$(SNAP)


$(SRC)/$(BUILD)/Makefile: apply
	cd $(SRC); mkdir -p $(BUILD); cd $(BUILD); \
	MACOSX_DEPLOYMENT_TARGET=$(MACOSX_DEPLOYMENT_TARGET) ../configure --prefix=$(PREFIX) \
                     --srcdir=$(SRC) \
                     --with-python=$(WP) \
                     --with-pic \
                     $(CONF_DBG)

compile: $(SRC)/$(BUILD)/Makefile
	cd $(SRC)/$(BUILD); MACOSX_DEPLOYMENT_TARGET=$(MACOSX_DEPLOYMENT_TARGET) $(MAKE); \
	MACOSX_DEPLOYMENT_TARGET=$(MACOSX_DEPLOYMENT_TARGET) $(MAKE) install

py:
	cd $(SRC)/python; \
	MACOSX_DEPLOYMENT_TARGET=$(MACOSX_DEPLOYMENT_TARGET) $(PYTHON) setup.py build --build-base=build_$(SNAP) $(DIST_OPT) \
                              install --force

build: expand compile py

snap: 
	cd $(BUILD_ROOT); \
        tar -cvzf $(LIBXML2)/libxml2-$(SNAP)-$(RELVER).tar.gz \
                  $(SNAP)/lib/libxml2* \
                  $(SNAP)/$(SITE)/*libxml2*; \
	$(MD5) $(LIBXML2)/libxml2-$(SNAP)-$(RELVER).tar.gz > $(LIBXML2)/libxml2-$(SNAP)-$(RELVER).tar.gz.md5

clean:
	cd $(SRC); rm -rf $(BUILD)

endif

apply: patches-$(VERSION)
	patch -Nup0 < patches-$(VERSION); echo ok

libxml2-$(VERSION).tar.gz:
	$(CURL) http://builds.o11n.org/external/libxml2-$(VERSION).tar.gz
	$(CURL) http://builds.o11n.org/external/libxml2-$(VERSION).tar.gz.md5

sources: libxml2-$(VERSION).tar.gz

libxml2-$(VERSION)-expanded: libxml2-$(VERSION).tar.gz
	tar xvzf libxml2-$(VERSION).tar.gz
	touch libxml2-$(VERSION)-expanded

expand: libxml2-$(VERSION)-expanded

upload: libxml2-$(SNAP)-$(RELVER).tar.gz
	scp libxml2-$(SNAP)-$(RELVER).tar.gz $(UPLOAD)
	scp libxml2-$(SNAP)-$(RELVER).tar.gz.md5 $(UPLOAD)

install: libxml2-$(SNAP)-$(RELVER).tar.gz
	tar -C $(CHANDLERBIN) -xvzf libxml2-$(SNAP)-$(RELVER).tar.gz
