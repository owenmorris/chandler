
VERSION=2.0
EPYDOC=$(BUILD_ROOT)/epydoc
SRC=$(EPYDOC)/epydoc-$(VERSION)

include $(BUILD_ROOT)/Makefile.inc

BUILD=build_$(SNAP)


build:
	cd $(SRC); \
	$(PYTHON) setup.py build --build-base=$(BUILD) $(DIST_OPT) \
                           install --force

expand: epydoc-$(VERSION).tar.gz
	tar xvzf epydoc-$(VERSION).tar.gz

snap: 
	cd $(BUILD_ROOT); \
        tar -cvzf $(EPYDOC)/$(SNAP).tar.gz \
                  $(SNAP)/$(SITE)/epydoc

clean:
	cd $(SRC); rm -rf $(BUILD)
