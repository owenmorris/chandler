
VERSION=1.2.1
DBXML=$(BUILD_ROOT)/persistence/dbxml
SRC=$(DBXML)/dbxml-$(VERSION)

include $(BUILD_ROOT)/Makefile.inc

ifeq ($(DEBUG),1)

CONF_DBG=--enable-debug
DIST_DBG=--debug

else

CONF_DBG=
DIST_DBG=

endif

BUILD=build_$(SNAP)


$(SRC)/$(BUILD)/Makefile:
	cd $(SRC); mkdir -p $(BUILD); cd $(BUILD); \
	../dist/configure --prefix=$(PREFIX)/dbxml \
                          --with-berkeleydb=$(PREFIX)/db \
                          --with-xerces=$(PREFIX) \
                          --with-pathan=$(PREFIX) \
                          $(CONF_DBG)

apply: $(SRC)/$(BUILD)/Makefile patches
	patch -Nup0 < patches; echo ok

build: apply
	cd $(SRC)/$(BUILD); $(MAKE); $(MAKE) install; \
	cd $(SRC)/src/python; \
	$(PYTHON) setup.py build --build-base=$(BUILD) \
                                 --with-berkeleydb=$(PREFIX)/db \
                                 --with-xerces=$(PREFIX) \
                                 --with-pathan=$(PREFIX) \
                                 $(DIST_DBG) \
                           install --force

expand: dbxml-$(VERSION).tar.gz
	tar xvzf dbxml-$(VERSION).tar.gz

snap: 
	cd $(BUILD_ROOT); \
        tar -cvzf $(DBXML)/$(SNAP).tar.gz \
                  $(SNAP)/dbxml/bin $(SNAP)/dbxml/lib \
                  $(SNAP)/$(SITE)/*dbxml*

clean:
	cd $(SRC); rm -rf $(BUILD); rm -rf src/python/$(BUILD)
