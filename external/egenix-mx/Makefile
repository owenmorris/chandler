
VERSION=2.1.0
EGENIX=$(BUILD_ROOT)/egenix-mx
SRC=$(EGENIX)/egenix-mx-base-$(VERSION)

include $(BUILD_ROOT)/Makefile.inc

BUILD=build_$(SNAP)


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
                  $(SNAP)/$(SITE)/mx \
            -X xcludes

clean:
	cd $(SRC); rm -rf $(BUILD)
