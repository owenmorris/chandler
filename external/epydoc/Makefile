
VERSION=2.1
EPYDOC=$(BUILD_ROOT)/epydoc
SRC=$(EPYDOC)/epydoc-$(VERSION)

include $(BUILD_ROOT)/Makefile.inc

BUILD=build_$(SNAP)

.PHONY: patches-$(VERSION)

apply: patches-$(VERSION)
	if [ -f patches-$(VERSION) ]; then \
            patch -Nup0 < patches-$(VERSION); echo ok; \
        fi

build: apply
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
