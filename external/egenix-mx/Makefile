
VERSION=2.0.4
EGENIX=$(BUILD_ROOT)/egenix-mx
SRC=$(EGENIX)/egenix-mx-base-$(VERSION)

ifeq ($(DEBUG),1)

DIST_OPT=--debug
PREFIX=$(BUILD_ROOT)/debug
SNAP=debug
PYTHON=$(PREFIX)/Library/Frameworks/Python.framework/Versions/2.3/bin/python_d

else

DIST_OPT=
PREFIX=$(BUILD_ROOT)/release
SNAP=release
PYTHON=$(PREFIX)/Library/Frameworks/Python.framework/Versions/2.3/bin/python

endif

BUILD=build_$(SNAP)


default: all

apply: patches
	patch -Nup0 < patches; echo ok

build: apply
	cd $(SRC); \
	$(PYTHON) setup.py build --build-base=$(BUILD) $(DIST_OPT) \
                           install --force

expand: egenix-mx-base-$(VERSION).tar.gz
	tar xvzf egenix-mx-base-$(VERSION).tar.gz

snap: 
	cd $(BUILD_ROOT); \
        tar -cvzf $(EGENIX)/$(SNAP).tar.gz \
                  $(SNAP)/Library/Frameworks/Python.framework/Versions/2.3/lib/python2.3/site-packages/mx

clean:
	cd $(SRC); rm -rf $(BUILD)

all: build
