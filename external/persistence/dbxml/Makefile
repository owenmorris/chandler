
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

ifeq ($(OS),Cygwin)

BUILD=build_win32

$(SRC)/$(BUILD)/Berkeley_DB_XML.sln:
	(cd win32; tar cf - *.sln *.vcproj) | (cd $(SRC)/$(BUILD); tar xf -)

apply: patches
	patch -Nup0 < patches; echo ok

build: $(SRC)/$(BUILD)/Berkeley_DB_XML.sln compile install py

compile:
	cd $(SRC)/$(BUILD); \
        devenv.com Berkeley_DB_XML.sln /project dbxml /build $(Snap)

install:
	(cd $(SRC)/$(BUILD)/$(Snap); \
         tar cf - *.dll) | (cd $(PREFIX)/bin; tar xvf -)
	(cd $(SRC)/$(BUILD)/$(Snap); \
         tar cf - *.lib *.exp) | (cd $(PREFIX)/lib; tar xvf -)

py: apply
	cd $(SRC)/src/python; \
	$(PYTHON) setup.py --with-berkeleydb=`cygpath -aw $(PREFIX)` \
                           --with-xerces=`cygpath -aw $(PREFIX)` \
                           --with-pathan=`cygpath -aw $(PREFIX)` \
                           build --build-base=$(BUILD) $(DIST_OPT) \
                           install --force

clean:
	cd $(SRC)/$(BUILD); \
        devenv.com Berkeley_DB_XML.sln /project dbxml /clean $(Snap)
	cd $(SRC)/src/python; rm -rf $(BUILD)
	rm -f $(SRC)/$(BUILD)/Berkeley_DB.sln

snap:
	cd $(BUILD_ROOT); \
        tar -cvzf $(DBXML)/$(SNAP).tar.gz \
                  $(SNAP)/bin/libdbxml*.dll \
                  $(SNAP)/$(SITE)/*dbxml*


else

BUILD=build_$(SNAP)


$(SRC)/$(BUILD)/Makefile:
	cd $(SRC); mkdir -p $(BUILD); cd $(BUILD); \
	../dist/configure --prefix=$(PREFIX)/dbxml \
                          --with-berkeleydb=$(PREFIX)/db \
                          --with-xerces=$(PREFIX) \
                          --with-pathan=$(PREFIX) \
                          --with-pic \
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

snap: 
	cd $(BUILD_ROOT); \
        tar -cvzf $(DBXML)/$(SNAP).tar.gz \
                  $(SNAP)/dbxml/bin $(SNAP)/dbxml/lib \
                  $(SNAP)/$(SITE)/*dbxml* \
            --exclude '*.a'

clean:
	cd $(SRC); rm -rf $(BUILD); rm -rf src/python/$(BUILD)

endif

expand: dbxml-$(VERSION).tar.gz
	tar xvzf dbxml-$(VERSION).tar.gz
