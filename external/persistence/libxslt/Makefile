
VERSION=1.1.2
RELVER=$(VERSION)-1
LIBXSLT=$(BUILD_ROOT)/persistence/libxslt
SRC=$(LIBXSLT)/libxslt-$(VERSION)

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
                            python=yes iconv=no static=yes 

compile: $(SRC)/$(BUILD)/config.msvc
	cd $(SRC)/win32; MAKEFLAGS=; \
	nmake -nologo -f Makefile.msvc BUILD_VERSION=$(SNAP) all install

installext:
	install $(SRC)/$(BUILD)/bin/xsltproc.exe $(PREFIX)/bin

py:
	cd $(SRC)/python; \
	$(PYTHON) winSetup.py build --build-base=build_$(SNAP) $(DIST_OPT) \
                              install --force

build: expand compile installext py

clean:
	cd $(SRC)/win32; MAKEFLAGS=; \
	nmake -nologo -f Makefile.msvc BUILD_VERSION=$(SNAP) clean
	cd $(SRC)/python; rm -rf build_$(SNAP)

snap: 
	cd $(BUILD_ROOT); \
        tar -cvzf $(LIBXSLT)/libxslt-$(SNAP)-$(RELVER).tar.gz \
                  $(SNAP)/$(SITE)/libxslt* $(SNAP)/bin/xsltproc.exe; \
	$(MD5) $(LIBXSLT)/libxslt-$(SNAP)-$(RELVER).tar.gz > $(LIBXSLT)/libxslt-$(SNAP)-$(RELVER).tar.gz.md5

else

ifeq ($(DEBUG),1)
CONF_DBG=--enable-debug
else
CONF_DBG=
endif

BUILD=build_$(SNAP)


$(SRC)/$(BUILD)/Makefile: apply
	cd $(SRC); mkdir -p $(BUILD); cd $(BUILD); \
	../configure --prefix=$(PREFIX) \
                     --srcdir=$(SRC) \
                     --with-libxml-prefix=$(PREFIX) \
                     --with-libxml-include-prefix=$(PREFIX) \
                     --with-libxml-lib-prefix=$(PREFIX) \
                     --with-python=$(WP) \
                     --with-pic \
                     $(CONF_DBG)

build: expand $(SRC)/$(BUILD)/Makefile
	cd $(SRC)/$(BUILD); $(MAKE); $(MAKE) install

snap: 
	cd $(BUILD_ROOT); \
        tar -cvzf $(LIBXSLT)/libxslt-$(SNAP)-$(RELVER).tar.gz \
                  $(SNAP)/lib/libxslt* $(SNAP)/lib/libexslt* \
                  $(SNAP)/$(SITE)/libxslt*; \
	$(MD5) $(LIBXSLT)/libxslt-$(SNAP)-$(RELVER).tar.gz > $(LIBXSLT)/libxslt-$(SNAP)-$(RELVER).tar.gz.md5

clean:
	cd $(SRC); rm -rf $(BUILD)

endif

libxslt-$(VERSION).tar.gz:
	$(CURL) http://builds.o11n.org/external/libxslt-$(VERSION).tar.gz
	$(CURL) http://builds.o11n.org/external/libxslt-$(VERSION).tar.gz.md5

sources: libxslt-$(VERSION).tar.gz

libxslt-$(VERSION)-expanded: libxslt-$(VERSION).tar.gz
	tar xvzf libxslt-$(VERSION).tar.gz
	touch libxslt-$(VERSION)-expanded

expand: libxslt-$(VERSION)-expanded

apply: patches
	patch -Nup0 < patches; echo ok;

upload: libxslt-$(SNAP)-$(RELVER).tar.gz
	scp libxslt-$(SNAP)-$(RELVER).tar.gz $(UPLOAD)
	scp libxslt-$(SNAP)-$(RELVER).tar.gz.md5 $(UPLOAD)

install: libxslt-$(SNAP)-$(RELVER).tar.gz
	tar -C $(CHANDLERBIN) -xvzf libxslt-$(SNAP)-$(RELVER).tar.gz
