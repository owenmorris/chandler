
VERSION=2_4_0
XERCESC=$(BUILD_ROOT)/persistence/xerces-c
SRC=$(XERCESC)/xerces-c-src$(VERSION)

ifeq ($(DEBUG),1)

CONF_DBG=-d
PREFIX=$(BUILD_ROOT)/debug
SNAP=debug

else

CONF_DBG=
PREFIX=$(BUILD_ROOT)/release
SNAP=release

endif

BUILD=build_$(SNAP)


default: all

$(SRC)/$(BUILD)/src/xercesc/Makefile:
	cd $(SRC); mkdir -p $(BUILD); cd $(BUILD); \
        ( cd $(SRC); tar -cf - obj src version.incl ) | tar -xf - ; \
        cd src/xercesc; \
        XERCESCROOT=$(SRC)/$(BUILD) \
	./runConfigure -pmacosx $(CONF_DBG) -P$(PREFIX) \
                       -minmem -nsocket -tnative -rnone

build: $(SRC)/$(BUILD)/src/xercesc/Makefile
	cd $(SRC)/$(BUILD)/src/xercesc; \
	XERCESCROOT=$(SRC)/$(BUILD) $(MAKE); \
	rm -f $(PREFIX)/lib/libxerces*; \
	XERCESCROOT=$(SRC)/$(BUILD) $(MAKE) install

snap: 
	cd $(BUILD_ROOT); \
        tar -cvzf $(XERCESC)/$(SNAP).tar.gz $(SNAP)/lib/libxerces*

clean:
	cd $(SRC); rm -rf $(BUILD)

all: build
