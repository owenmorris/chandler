
VERSION=2_4_0
XERCESC=$(BUILD_ROOT)/persistence/xerces-c
SRC=$(XERCESC)/xerces-c-src$(VERSION)

include $(BUILD_ROOT)/Makefile.inc

ifeq ($(DEBUG),1)
CONF_DBG=-d
else
CONF_DBG=
endif

ifeq ($(OS),Darwin)
CONF_OS=-pmacosx
else
CONF_OS=-plinux
endif

BUILD=build_$(SNAP)


$(SRC)/$(BUILD)/src/xercesc/Makefile:
	cd $(SRC); mkdir -p $(BUILD); cd $(BUILD); \
        ( cd $(SRC); tar -cf - obj src version.incl ) | tar -xf - ; \
        cd src/xercesc; \
        XERCESCROOT=$(SRC)/$(BUILD) \
	./runConfigure $(CONF_OS) $(CONF_DBG) -P$(PREFIX) \
                       -minmem -nsocket -tnative -rnone

build: $(SRC)/$(BUILD)/src/xercesc/Makefile
	cd $(SRC)/$(BUILD)/src/xercesc; \
	XERCESCROOT=$(SRC)/$(BUILD) $(MAKE); \
	rm -f $(PREFIX)/lib/libxerces*; \
	XERCESCROOT=$(SRC)/$(BUILD) $(MAKE) install

expand: xerces-c-src$(VERSION).tar.gz
	tar xvzf xerces-c-src$(VERSION).tar.gz

snap: 
	cd $(BUILD_ROOT); \
        tar -cvzf $(XERCESC)/$(SNAP).tar.gz $(SNAP)/lib/libxerces*

clean:
	cd $(SRC); rm -rf $(BUILD)
