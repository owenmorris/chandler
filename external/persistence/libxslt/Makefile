
VERSION=1.1.2
LIBXSLT=$(BUILD_ROOT)/persistence/libxslt
SRC=$(LIBXSLT)/libxslt-$(VERSION)

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
                     --with-libxml-prefix=$(PREFIX) \
                     --with-libxml-include-prefix=$(PREFIX) \
                     --with-libxml-lib-prefix=$(PREFIX) \
                     --with-python=$(WP) \
                     $(CONF_DBG)

build: $(SRC)/$(BUILD)/Makefile
	cd $(SRC)/$(BUILD); $(MAKE); $(MAKE) install

expand: libxslt-$(VERSION).tar.gz
	tar xvzf libxslt-$(VERSION).tar.gz

snap: 
	cd $(BUILD_ROOT); \
        tar -cvzf $(LIBXSLT)/$(SNAP).tar.gz \
                  $(SNAP)/lib/libxslt* $(SNAP)/lib/libexslt* \
                  $(SNAP)/$(SITE)/libxslt*

clean:
	cd $(SRC); rm -rf $(BUILD)
