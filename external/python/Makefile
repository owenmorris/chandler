
VERSION=2.3.3
PYTHON=$(BUILD_ROOT)/python
SRC=$(PYTHON)/Python-$(VERSION)

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

$(SRC)/$(BUILD)/Makefile:
	cd $(SRC); mkdir -p $(BUILD); cd $(BUILD); \
	../configure --prefix=$(PREFIX) \
                     --enable-framework=$(PREFIX)/Library/Frameworks \
                     LDFLAGS=-F$(PREFIX)/Library/Frameworks \
                     $(CONF_DBG)


apply: $(SRC)/$(BUILD)/Makefile patches
	patch -Nup0 < patches; echo ok

build: apply
	cd $(SRC)/$(BUILD); \
        $(MAKE) DB=$(PREFIX)/db $(COMP_OPT) frameworkinstallframework; \
        $(MAKE) DB=$(PREFIX)/db $(COMP_OPT) frameworkinstallapps

expand: Python-$(VERSION).tgz
	tar xvzf Python-$(VERSION).tgz

snap: 
	cd $(BUILD_ROOT); \
        tar -cvzf $(PYTHON)/$(SNAP).tar.gz \
                  $(SNAP)/Library/Frameworks/Python.framework \
            -X $(PYTHON)/xcludes

clean:
	cd $(SRC); rm -rf $(BUILD)

all: build
