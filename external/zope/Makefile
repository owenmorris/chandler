
VERSION=3.0.0b1
ZOPE=$(BUILD_ROOT)/zope
SRC=$(ZOPE)/ZopeInterface-$(VERSION)

include $(BUILD_ROOT)/Makefile.inc

BUILD=build_$(SNAP)

build: 
	cd $(SRC); \
	$(PYTHON) setup.py build --build-base=$(BUILD) \
                           install --force

expand: ZopeInterface-$(VERSION).tgz
	tar xzvf ZopeInterface-$(VERSION).tgz

snap: 
	cd $(BUILD_ROOT); \
	tar -cvzf $(ZOPE)/$(SNAP).tar.gz \
			  $(SNAP)/$(SITE)/zope 

clean:
	rm -rf  $(SRC)/$(BUILD)

