
VERSION=r11245
TWISTED=$(BUILD_ROOT)/twisted
SRC=$(TWISTED)/Twisted-$(VERSION)

include $(BUILD_ROOT)/Makefile.inc

BUILD=build_$(SNAP)

# Temporary, use to test Twisted with M2Crypto
applym2:
	cd $(SRC); \
	patch -p0<../m2-patches

apply: patches-$(VERSION)
	patch -Nup0 < patches-$(VERSION);echo ok

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
			  $(SNAP)/$(SITE)/twisted 

endif

clean:
	rm -rf  $(SRC)/$(BUILD)

