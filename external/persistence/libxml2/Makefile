
VERSION=2.6.10
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

build: compile py

clean:
	cd $(SRC)/win32; rm -rf $(SNAP)
	cd $(SRC)/python; rm -rf build_$(SNAP)

snap: 
	cd $(BUILD_ROOT); \
        tar -cvzf $(LIBXML2)/$(SNAP).tar.gz \
                  $(SNAP)/$(SITE)/libxml2*

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
                     --with-python=$(WP) \
                     $(CONF_DBG)

build: $(SRC)/$(BUILD)/Makefile
	cd $(SRC)/$(BUILD); $(MAKE); $(MAKE) install

snap: 
	cd $(BUILD_ROOT); \
        tar -cvzf $(LIBXML2)/$(SNAP).tar.gz \
                  $(SNAP)/lib/libxml2* \
                  $(SNAP)/$(SITE)/libxml2*

clean:
	cd $(SRC); rm -rf $(BUILD)

endif

apply: patches
	patch -Nup0 < patches-$(VERSION); echo ok

expand: libxml2-$(VERSION).tar.gz
	tar xvzf libxml2-$(VERSION).tar.gz
