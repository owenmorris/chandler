
VERSION=2.3.3
BZIP2VERSION=1.0.2
PYTHON=$(BUILD_ROOT)/python
SRC=$(PYTHON)/Python-$(VERSION)
OS=$(shell uname)

ifeq ($(DEBUG),1)

CONF_DBG=--with-suffix=_d --with-pydebug
COMP_OPT=OPT=-g
PREFIX=$(BUILD_ROOT)/debug
SNAP=debug

else

CONF_DBG=
COMP_OPT=
PREFIX=$(BUILD_ROOT)/release
SNAP=release

endif

BUILD=build_$(SNAP)


default: all

ifeq ($(OS),Darwin)

$(SRC)/$(BUILD)/Makefile:
	cd $(SRC); mkdir -p $(BUILD); cd $(BUILD); \
	../configure --prefix=$(PREFIX) $(CONF_DBG) \
                     --enable-framework=$(PREFIX)/Library/Frameworks \
                     LDFLAGS=-F$(PREFIX)/Library/Frameworks

build: apply
	cd $(SRC)/$(BUILD); \
        $(MAKE) DB=$(PREFIX)/db $(COMP_OPT) frameworkinstallframework; \
        $(MAKE) DB=$(PREFIX)/db $(COMP_OPT) frameworkinstallapps

snap: 
	cd $(BUILD_ROOT); \
        tar -cvzf $(PYTHON)/$(SNAP).tar.gz \
                  $(SNAP)/Library/Frameworks/Python.framework \
            -X $(PYTHON)/xcludes

expand: Python-$(VERSION).tgz
	tar xvzf Python-$(VERSION).tgz

else

$(SRC)/$(BUILD)/Makefile:
	cd $(SRC); mkdir -p $(BUILD); cd $(BUILD); \
	../configure --prefix=$(PREFIX) $(CONF_DBG)

bz2: bzip2-$(BZIP2VERSION)/libbz2.a
	cd bzip2-$(BZIP2VERSION); \
        make libbz2.a; \
        install libbz2.a $(PREFIX)/lib; \
        install bzlib.h $(PREFIX)/include

build: bz2 apply
	cd $(SRC)/$(BUILD); \
	$(MAKE) DB=$(PREFIX)/db $(COMP_OPT) install

snap: 
	cd $(BUILD_ROOT); \
        tar -cvzf $(PYTHON)/$(SNAP).tar.gz \
                  $(SNAP)/bin/idle $(SNAP)/bin/python* $(SNAP)/lib/python* \
            -X $(PYTHON)/xcludes

expand: Python-$(VERSION).tgz
	tar xvzf Python-$(VERSION).tgz; \
        tar xvzf bzip2-$(BZIP2VERSION).tar.gz

endif


apply: $(SRC)/$(BUILD)/Makefile patches
	patch -Nup0 < patches; echo ok

clean:
	cd $(SRC); rm -rf $(BUILD)

all: build
