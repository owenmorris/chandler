
VERSION=0.8.3
PYXML=$(BUILD_ROOT)/pyxml
SRC=$(PYXML)/PyXML-$(VERSION)

include $(BUILD_ROOT)/Makefile.inc

BUILD=build_$(SNAP)


build:
	cd $(SRC); \
	$(PYTHON) setup.py build --build-base=$(BUILD) $(DIST_OPT) \
                           install --force

expand: PyXML-$(VERSION).tar.gz
	tar xvzf PyXML-$(VERSION).tar.gz

snap: 
	cd $(BUILD_ROOT); \
        tar -cvzf $(PYXML)/$(SNAP).tar.gz \
                  $(SNAP)/$(SITE)/_xmlplus

clean:
	cd $(SRC); rm -rf $(BUILD)
