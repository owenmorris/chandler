
VERSION=2.6.3
LIBXML2=$(BUILD_ROOT)/persistence/libxml2
SRC=$(LIBXML2)/libxml2-$(VERSION)

include $(BUILD_ROOT)/Makefile.inc

ifeq ($(DEBUG),1)
CONF_DBG=--enable-debug
else
CONF_DBG=
endif

ifeq ($(OS),Darwin)
WP=$(PREFIX)/$(FRAMEWORK)
else
WP=$(PREFIX)
endif

BUILD=build_$(SNAP)


$(SRC)/$(BUILD)/Makefile: patches
	patch -Nup0 < patches; echo ok; \
	cd $(SRC); mkdir -p $(BUILD); cd $(BUILD); \
	../configure --prefix=$(PREFIX) \
                     --srcdir=$(SRC) \
                     --with-python=$(WP) \
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
