
VERSION=1.3.0
TWISTED=$(BUILD_ROOT)/twisted
SRC=$(TWISTED)/Twisted-$(VERSION)

include $(BUILD_ROOT)/Makefile.inc

BUILD=build_$(SNAP)

.PHONY: patches-$(VERSION)

apply: expand patches-$(VERSION)
	if [ -f patches-$(VERSION) ]; then \
            patch -Nup0 < patches-$(VERSION); echo ok; \
        fi

build: apply
	cd $(SRC); \
	$(PYTHON) setup.py build --build-base=$(BUILD) $(DIST_OPT) \
                           install --force

expand: Twisted-$(VERSION).tar.gz
	tar xvzf Twisted-$(VERSION).tar.gz

ifeq ($(OS),Cygwin)

snap: 
	cd $(BUILD_ROOT); \
	tar -cvzf $(TWISTED)/$(SNAP).tar.gz \
			  $(SNAP)/$(SITE)/twisted \
			  $(SNAP)/bin/Scripts

else


snap: 
	cd $(BUILD_ROOT); \
	tar -cvzf $(TWISTED)/$(SNAP).tar.gz \
			  $(SNAP)/$(SITE)/twisted \
			  $(SNAP)/bin/ckeygen \
			  $(SNAP)/bin/conch \
			  $(SNAP)/bin/im \
			  $(SNAP)/bin/lore \
			  $(SNAP)/bin/mailmail \
			  $(SNAP)/bin/manhole \
			  $(SNAP)/bin/mktap \
			  $(SNAP)/bin/t-im \
			  $(SNAP)/bin/tap2deb \
			  $(SNAP)/bin/tap2rpm \
			  $(SNAP)/bin/tapconvert \
			  $(SNAP)/bin/tkconch \
			  $(SNAP)/bin/tkmktap \
			  $(SNAP)/bin/trial \
			  $(SNAP)/bin/twistd
			  $(SNAP)/bin/websetroot \

endif

clean:
	cd $(SRC); rm -rf $(BUILD)

