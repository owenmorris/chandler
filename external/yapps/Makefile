
VERSION=2.1.1
YAPPS=$(BUILD_ROOT)/yapps
SRC=$(YAPPS)/yapps3

include $(BUILD_ROOT)/Makefile.inc

BUILD=build_$(SNAP)

build: apply
	mkdir -p $(PREFIX)/$(SITE)/yapps; \
	cp -p $(SRC)/yapps2.py $(SRC)/yappsrt.py $(SRC)/grammar.py $(SRC)/parsetree.py $(PREFIX)/$(SITE)/yapps
	cp -p __init__.py $(PREFIX)/$(SITE)/yapps

expand: 
	unzip -o yapps$(VERSION).zip

snap: 
	cd $(BUILD_ROOT); \
	tar -cvzf $(YAPPS)/$(SNAP).tar.gz $(SNAP)/$(SITE)/yapps

apply: 
	patch -Nup0 < patches-$(VERSION); echo ok

clean:
	rm -rf  $(SRC)/$(BUILD)

patches:
	diff -u yapps3/grammar.py yapps3-patched/grammar.py > patches-$(VERSION); true
	diff -u yapps3/yapps2.py yapps3-patched/yapps2.py >> patches-$(VERSION); true
	diff -u yapps3/parsetree.py yapps3-patched/parsetree.py >> patches-$(VERSION); true
	diff -u yapps3/yapps_grammar.py yapps3-patched/yapps_grammar.py >> patches-$(VERSION); true
