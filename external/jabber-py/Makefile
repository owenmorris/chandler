
VERSION=0.4-0
JABBERPY=$(BUILD_ROOT)/jabber-py
SRC=$(JABBERPY)/jabberpy$(VERSION)

include $(BUILD_ROOT)/Makefile.inc

BUILD=build_$(SNAP)


apply: patches
	patch -Nup0 < patches; echo ok

build: apply
	cd $(SRC); \
	$(PYTHON) setup.py build --build-base=$(BUILD) $(DIST_OPT) \
                           install --force

expand: jabberpy$(VERSION).tar.gz
	tar xvzf jabberpy$(VERSION).tar.gz

snap: 
	cd $(BUILD_ROOT); \
        tar -cvzf $(JABBERPY)/$(SNAP).tar.gz \
                  $(SNAP)/$(SITE)/jabber.py* \
                  $(SNAP)/$(SITE)/xmlstream.py*

clean:
	cd $(SRC); rm -rf $(BUILD)
