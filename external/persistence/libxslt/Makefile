
VERSION=1.1.2
LIBXSLT=$(BUILD_ROOT)/persistence/libxslt
SRC=$(LIBXSLT)/libxslt-$(VERSION)

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
                     --with-libxml-prefix=$(PREFIX) \
                     --with-libxml-include-prefix=$(PREFIX) \
                     --with-libxml-lib-prefix=$(PREFIX) \
                     --with-python=$(PREFIX)/Library/Frameworks/Python.framework/Versions/Current \
                     $(CONF_DBG)

build: $(SRC)/$(BUILD)/Makefile
	cd $(SRC)/$(BUILD); $(MAKE); $(MAKE) install

expand: libxslt-$(VERSION).tar.gz
	tar xvzf libxslt-$(VERSION).tar.gz

snap: 
	cd $(BUILD_ROOT); \
        tar -cvzf $(LIBXSLT)/$(SNAP).tar.gz \
                  $(SNAP)/lib/libxslt* $(SNAP)/lib/libexslt* \
                  $(SNAP)/Library/Frameworks/Python.framework/Versions/2.3/lib/python2.3/site-packages/libxslt*

clean:
	cd $(SRC); rm -rf $(BUILD)

all: build
