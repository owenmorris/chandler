
VERSION=r11303
RELVER=$(VERSION)-1
TWISTED=$(BUILD_ROOT)/twisted
SRC=$(TWISTED)/Twisted-$(VERSION)

include $(BUILD_ROOT)/Makefile.inc

BUILD=build_$(SNAP)

# Temporary until integrated into Twisted
applysmtp:
	patch -Nup0 < smtp-patches; echo ok

applyimap4:
	patch -Nup0 < imap4-patches; echo ok

# Temporary until refactored and integrated into Twisted
applym2:
	rm -f $(SRC)/twisted/internet/m2ssl.py ; \
	cd $(SRC); \
	patch -Nup0<../m2-patches;echo ok

apply: patches-$(VERSION)
	patch -Nup0 < patches-$(VERSION);echo ok

build: expand apply applym2 applysmtp applyimap4
	cd $(SRC); \
	$(PYTHON) setup.py build --build-base=$(BUILD) $(DIST_OPT) \
                           install --force

Twisted-$(VERSION).tar.gz:
	$(CURL) http://builds.o11n.org/external/Twisted-$(VERSION).tar.gz
	$(CURL) http://builds.o11n.org/external/Twisted-$(VERSION).tar.gz.md5

sources: Twisted-$(VERSION).tar.gz

Twisted-$(VERSION)-expanded: Twisted-$(VERSION).tar.gz
	tar xvzf Twisted-$(VERSION).tar.gz
	touch Twisted-$(VERSION)-expanded

expand: Twisted-$(VERSION)-expanded

snap: 
	cd $(BUILD_ROOT); \
	tar -cvzf $(TWISTED)/twisted-$(SNAP)-$(RELVER).tar.gz \
		$(SNAP)/$(SITE)/twisted \
		--exclude test; \
	$(MD5) $(TWISTED)/twisted-$(SNAP)-$(RELVER).tar.gz > $(TWISTED)/twisted-$(SNAP)-$(RELVER).tar.gz.md5

install: twisted-$(SNAP)-$(RELVER).tar.gz
	tar -C $(CHANDLERBIN) -xvzf twisted-$(SNAP)-$(RELVER).tar.gz

upload: twisted-$(SNAP)-$(RELVER).tar.gz
	scp twisted-$(SNAP)-$(RELVER).tar.gz $(UPLOAD)
	scp twisted-$(SNAP)-$(RELVER).tar.gz.md5 $(UPLOAD)

clean:
	rm -rf  $(SRC)/$(BUILD)

