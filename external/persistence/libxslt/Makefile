
VERSION=1.1.2
LIBXSLT=$(BUILD_ROOT)/persistence/libxslt
SRC=$(LIBXSLT)/libxslt-$(VERSION)
OS=$(shell uname)

ifeq ($(DEBUG),1)

CONF_DBG=--enable-debug
DIST_DBG=--debug
PREFIX=$(BUILD_ROOT)/debug
SNAP=debug

else

CONF_DBG=
DIST_DBG=
PREFIX=$(BUILD_ROOT)/release
SNAP=release

endif

ifeq ($(OS),Darwin)

PYTHON=$(PREFIX)/Library/Frameworks/Python.framework/Versions/Current
SITE=Library/Frameworks/Python.framework/Versions/2.3/lib/python2.3/site-packages

else

PYTHON=$(PREFIX)
SITE=lib/python2.3/site-packages

endif

BUILD=build_$(SNAP)


default: all

$(SRC)/$(BUILD)/Makefile: patches
	patch -Nup0 < patches; echo ok; \
	cd $(SRC); mkdir -p $(BUILD); cd $(BUILD); \
	../configure --prefix=$(PREFIX) \
                     --srcdir=$(SRC) \
                     --with-libxml-prefix=$(PREFIX) \
                     --with-libxml-include-prefix=$(PREFIX) \
                     --with-libxml-lib-prefix=$(PREFIX) \
                     --with-python=$(PYTHON) \
                     $(CONF_DBG)

build: $(SRC)/$(BUILD)/Makefile
	cd $(SRC)/$(BUILD); $(MAKE); $(MAKE) install

expand: libxslt-$(VERSION).tar.gz
	tar xvzf libxslt-$(VERSION).tar.gz

snap: 
	cd $(BUILD_ROOT); \
        tar -cvzf $(LIBXSLT)/$(SNAP).tar.gz \
                  $(SNAP)/lib/libxslt* $(SNAP)/lib/libexslt* \
                  $(SNAP)/$(SITE)/libxslt*

clean:
	cd $(SRC); rm -rf $(BUILD)

all: build
