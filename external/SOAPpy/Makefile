
VERSION=0.10.2
SOAPPY=$(BUILD_ROOT)/SOAPpy
SRC=$(SOAPPY)/SOAPpy-$(VERSION)

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

expand: SOAPpy-$(VERSION).tar.gz
	tar xvzf SOAPpy-$(VERSION).tar.gz

snap: 
	cd $(BUILD_ROOT); \
        tar -cvzf $(SOAPPY)/$(SNAP).tar.gz \
                  $(SNAP)/Library/Frameworks/Python.framework/Versions/2.3/lib/python2.3/site-packages/SOAPpy

clean:
	cd $(SRC); rm -rf $(BUILD)

all: build
