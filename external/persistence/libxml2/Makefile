
VERSION=2.6.3
LIBXML2=$(BUILD_ROOT)/persistence/libxml2
SRC=$(LIBXML2)/libxml2-$(VERSION)
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
                     --with-python=$(PYTHON) \
                     $(CONF_DBG)

build: $(SRC)/$(BUILD)/Makefile
	cd $(SRC)/$(BUILD); $(MAKE); $(MAKE) install

expand: libxml2-$(VERSION).tar.gz
	tar xvzf libxml2-$(VERSION).tar.gz

snap: 
	cd $(BUILD_ROOT); \
        tar -cvzf $(LIBXML2)/$(SNAP).tar.gz \
                  $(SNAP)/lib/libxml2* \
                  $(SNAP)/$(SITE)/libxml2*

clean:
	cd $(SRC); rm -rf $(BUILD)

all: build
