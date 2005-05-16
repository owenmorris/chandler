
VERSION=2.1.1
RELVER=$(VERSION)-3
YAPPS=$(BUILD_ROOT)/yapps
SRC=$(YAPPS)/yapps3

include $(BUILD_ROOT)/Makefile.inc

BUILD=build_$(SNAP)

build: expand apply
	mkdir -p $(PREFIX)/$(SITE)/yapps; \
	cp -p $(SRC)/yapps2.py $(SRC)/yappsrt.py $(SRC)/grammar.py $(SRC)/parsetree.py $(PREFIX)/$(SITE)/yapps
	cp -p __init__.py $(PREFIX)/$(SITE)/yapps

yapps$(VERSION).zip:
	$(CURL) http://builds.o11n.org/external/yapps$(VERSION).zip
	$(CURL) http://builds.o11n.org/external/yapps$(VERSION).zip.md5

sources: yapps$(VERSION).zip

yapps$(VERSION)-expanded: yapps$(VERSION).zip
	unzip -o yapps$(VERSION).zip
	touch yapps$(VERSION)-expanded

expand: yapps$(VERSION)-expanded

snap: 
	cd $(BUILD_ROOT); \
	find $(SNAP)/$(SITE)/yapps -name "*.pyc" | xargs rm -f; \
	find $(SNAP)/$(SITE)/yapps -name "*.pyo" | xargs rm -f; \
	tar -cvzf $(YAPPS)/yapps-$(SNAP)-$(RELVER).tar.gz \
		$(SNAP)/$(SITE)/yapps; \
	$(MD5) $(YAPPS)/yapps-$(SNAP)-$(RELVER).tar.gz > $(YAPPS)/yapps-$(SNAP)-$(RELVER).tar.gz.md5

install: yapps-$(SNAP)-$(RELVER).tar.gz
	tar -C $(CHANDLERBIN) -xvzf yapps-$(SNAP)-$(RELVER).tar.gz

upload: yapps-$(SNAP)-$(RELVER).tar.gz
	scp yapps-$(SNAP)-$(RELVER).tar.gz $(UPLOAD)
	scp yapps-$(SNAP)-$(RELVER).tar.gz.md5 $(UPLOAD)

apply: 
	patch -Nup0 < patches-$(VERSION); echo ok

clean:
	rm -rf  $(SRC)/$(BUILD)

patches:
	diff -u yapps3/grammar.py yapps3-patched/grammar.py > patches-$(VERSION); true
	diff -u yapps3/yapps2.py yapps3-patched/yapps2.py >> patches-$(VERSION); true
	diff -u yapps3/parsetree.py yapps3-patched/parsetree.py >> patches-$(VERSION); true
	diff -u yapps3/yapps_grammar.py yapps3-patched/yapps_grammar.py >> patches-$(VERSION); true

_realclean::
	rm -f yapps$(VERSION)*
