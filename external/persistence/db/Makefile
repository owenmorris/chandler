
VERSION=4.2.52
DB=$(BUILD_ROOT)/persistence/db
SRC=$(DB)/db-$(VERSION)

ifeq ($(DEBUG),1)

CONF_DBG=--enable-debug
PREFIX=$(BUILD_ROOT)/debug
SNAP=debug

else

CONF_DBG=
PREFIX=$(BUILD_ROOT)/release
SNAP=release

endif

BUILD=build_$(SNAP)


default: all

$(SRC)/$(BUILD)/Makefile: patches
	patch -Nup0 < patches; echo ok; \
	cd $(SRC); mkdir -p $(BUILD); cd $(BUILD); \
	../dist/configure --prefix=$(PREFIX)/db \
                          --enable-cxx $(CONF_DBG)

build: $(SRC)/$(BUILD)/Makefile
	cd $(SRC)/$(BUILD); $(MAKE); $(MAKE) install

expand: db-$(VERSION).tar.gz
	tar xvzf db-$(VERSION).tar.gz

snap: 
	cd $(BUILD_ROOT); \
        tar -cvzf $(DB)/$(SNAP).tar.gz $(SNAP)/db/bin $(SNAP)/db/lib

clean:
	cd $(SRC); rm -rf $(BUILD)

all: build
