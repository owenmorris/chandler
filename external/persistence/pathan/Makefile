
VERSION=1.2
PATHAN=$(BUILD_ROOT)/persistence/pathan
XERCESC=$(BUILD_ROOT)/persistence/xerces-c/xerces-c-src2_4_0
SRC=$(PATHAN)/libpathan-$(VERSION)

include $(BUILD_ROOT)/Makefile.inc

ifeq ($(DEBUG),1)
CONF_DBG=--compiletype=debug
else
CONF_DBG=
endif

BUILD=build_$(SNAP)


$(SRC)/$(BUILD)/Makefile.defs:
	cd $(SRC); mkdir -p $(BUILD); cd $(BUILD); \
        ( cd $(SRC); tar -cf - autotools examples src util \
                               aclocal.m4 configure configure.in \
                               Makefile Makefile.defs.in Makefile.deps \
                               Makefile.plat runConfigure ) | tar -xf - ; \
        XERCESCROOT=$(XERCESC)/$(BUILD) \
	./runConfigure --prefix=$(PREFIX) $(CONF_DBG)

build: $(SRC)/$(BUILD)/Makefile.defs
	cd $(SRC)/$(BUILD); \
	XERCESCROOT=$(XERCESC)/$(BUILD) $(MAKE); \
	XERCESCROOT=$(XERCESC)/$(BUILD) $(MAKE) install

expand: libpathan-$(VERSION)-2-src.tar.gz
	tar xvzf libpathan-$(VERSION)-2-src.tar.gz

snap: 
	cd $(BUILD_ROOT); \
        tar -cvzf $(PATHAN)/$(SNAP).tar.gz $(SNAP)/lib/libpathan*

clean:
	cd $(SRC); rm -rf $(BUILD)
