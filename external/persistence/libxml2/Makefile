
VERSION=2.6.3
LIBXML2=$(BUILD_ROOT)/persistence/libxml2
SRC=$(LIBXML2)/libxml2-$(VERSION)

ifeq ($(DEBUG),1)

CONF_DBG=--enable-debug
DIST_DBG=--debug
PREFIX=$(BUILD_ROOT)/debug
SNAP=debug
PYTHON=$(PREFIX)/Library/Frameworks/Python.framework/Versions/2.3/bin/python_d

else

CONF_DBG=
DIST_DBG=
PREFIX=$(BUILD_ROOT)/release
SNAP=release
PYTHON=$(PREFIX)/Library/Frameworks/Python.framework/Versions/2.3/bin/python

endif

BUILD=build_$(SNAP)


default: all

$(SRC)/$(BUILD)/Makefile: patches
	patch -Nup0 < patches; echo ok; \
	cd $(SRC); mkdir -p $(BUILD); cd $(BUILD); \
	../configure --prefix=$(PREFIX) \
                     --srcdir=$(SRC) \
                     --with-python=$(PREFIX)/Library/Frameworks/Python.framework/Versions/Current \
                     $(CONF_DBG)

build: $(SRC)/$(BUILD)/Makefile
	cd $(SRC)/$(BUILD); $(MAKE); $(MAKE) install

snap: 
	cd $(BUILD_ROOT); \
        tar -cvzf $(LIBXML2)/$(SNAP).tar.gz \
                  $(SNAP)/lib/libxml2* \
                  $(SNAP)/Library/Frameworks/Python.framework/Versions/2.3/lib/python2.3/site-packages/libxml2*

clean:
	cd $(SRC); rm -rf $(BUILD)

all: build
