
VERSION=1.2.1
DBXML=$(BUILD_ROOT)/persistence/dbxml
SRC=$(DBXML)/dbxml-$(VERSION)

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

$(SRC)/$(BUILD)/Makefile:
	cd $(SRC); mkdir -p $(BUILD); cd $(BUILD); \
	../dist/configure --prefix=$(PREFIX)/dbxml \
                          --with-berkeley-db=$(PREFIX)/db \
                          --with-xerces=$(PREFIX) \
                          --with-pathan=$(PREFIX) \
                          $(CONF_DBG)

apply: $(SRC)/$(BUILD)/Makefile patches
	patch -Nup0 < patches; echo ok

build: apply
	cd $(SRC)/$(BUILD); $(MAKE); $(MAKE) install; \
	cd $(SRC)/src/python; \
	$(PYTHON) setup.py build --build-base=$(BUILD) \
                                 --with-berkeley-db=$(PREFIX)/db \
                                 --with-xerces=$(PREFIX) \
                                 --with-pathan=$(PREFIX) \
                                 $(DIST_DBG) \
                           install --force

snap: 
	cd $(BUILD_ROOT); \
        tar -cvzf $(DBXML)/$(SNAP).tar.gz \
                  $(SNAP)/dbxml/bin $(SNAP)/dbxml/lib \
                  $(SNAP)/Library/Frameworks/Python.framework/Versions/2.3/lib/python2.3/site-packages/*dbxml*

clean:
	cd $(SRC); rm -rf $(BUILD); rm -rf src/python/$(BUILD)

all: build
