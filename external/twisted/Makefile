
VERSION=r11303
TWISTED=$(BUILD_ROOT)/twisted
SRC=$(TWISTED)/Twisted-$(VERSION)

include $(BUILD_ROOT)/Makefile.inc

BUILD=build_$(SNAP)

# Temporary until integrated into Twisted
applysmtp:
	patch $(SRC)/twisted/mail/smtp.py smtp-patches; echo ok

# Temporary until refactored and integrated into Twisted
applym2:
	rm -f $(SRC)/twisted/internet/m2ssl.py ; \
	cd $(SRC); \
	patch -Nup0<../m2-patches;echo ok

apply: patches-$(VERSION)
	patch -Nup0 < patches-$(VERSION);echo ok

build: apply applym2 applysmtp
	cd $(SRC); \
	$(PYTHON) setup.py build --build-base=$(BUILD) $(DIST_OPT) \
                           install --force

expand: Twisted-$(VERSION).tar.gz
	tar xvzf Twisted-$(VERSION).tar.gz

snap: 
	cd $(BUILD_ROOT); \
	tar -cvzf $(TWISTED)/$(SNAP).tar.gz $(SNAP)/$(SITE)/twisted \
            --exclude test

clean:
	rm -rf  $(SRC)/$(BUILD)

