
VERSION=1.1.2
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

install:
	install $(SRC)/$(BUILD)/bin/xsltproc.exe $(PREFIX)/bin

py:
	cd $(SRC)/python; \
	$(PYTHON) winSetup.py build --build-base=build_$(SNAP) $(DIST_DBG) \
                              install --force

build: compile install py

clean:
	cd $(SRC)/win32; MAKEFLAGS=; \
	nmake -nologo -f Makefile.msvc BUILD_VERSION=$(SNAP) clean
	cd $(SRC)/python; rm -rf build_$(SNAP)

snap: 
	cd $(BUILD_ROOT); \
        tar -cvzf $(LIBXSLT)/$(SNAP).tar.gz \
                  $(SNAP)/$(SITE)/libxslt* $(SNAP)/bin/xsltproc.exe

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
                     $(CONF_DBG)

build: $(SRC)/$(BUILD)/Makefile
	cd $(SRC)/$(BUILD); $(MAKE); $(MAKE) install

snap: 
	cd $(BUILD_ROOT); \
        tar -cvzf $(LIBXSLT)/$(SNAP).tar.gz \
                  $(SNAP)/lib/libxslt* $(SNAP)/lib/libexslt* \
                  $(SNAP)/$(SITE)/libxslt*

clean:
	cd $(SRC); rm -rf $(BUILD)

endif

expand: libxslt-$(VERSION).tar.gz
	tar xvzf libxslt-$(VERSION).tar.gz

apply: patches
	patch -Nup0 < patches; echo ok;
