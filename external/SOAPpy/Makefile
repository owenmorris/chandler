
VERSION=0.10.2
SOAPPY=$(BUILD_ROOT)/SOAPpy
SRC=$(SOAPPY)/SOAPpy-$(VERSION)

include $(BUILD_ROOT)/Makefile.inc

BUILD=build_$(SNAP)


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
                  $(SNAP)/$(SITE)/SOAPpy

clean:
	cd $(SRC); rm -rf $(BUILD)
