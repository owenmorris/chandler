
VERSION=1.2
PATHAN=$(BUILD_ROOT)/persistence/pathan
XERCESC=$(BUILD_ROOT)/persistence/xerces-c/xerces-c-src2_4_0
SRC=$(PATHAN)/libpathan-$(VERSION)

ifeq ($(DEBUG),1)

CONF_DBG=--compiletype=debug
PREFIX=$(BUILD_ROOT)/debug
SNAP=debug

else

CONF_DBG=
PREFIX=$(BUILD_ROOT)/release
SNAP=release

endif

BUILD=build_$(SNAP)


default: all

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

snap: 
	cd $(BUILD_ROOT); \
        tar -cvzf $(PATHAN)/$(SNAP).tar.gz $(SNAP)/lib/libpathan*

clean:
	cd $(SRC); rm -rf $(BUILD)

all: build
