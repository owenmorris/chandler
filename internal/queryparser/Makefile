
include ../Makefile.inc

RELVER=0.4-4
QP=$(INTERNAL)/queryparser

ifeq ($(OS),Cygwin)
TOOLPATH="`cygpath -aw $(BUILD_ROOT)/$(SNAP)/$(SITE)/yapps/yapps2.py`"
GRAMMAR_PATH="`cygpath -aw $(SRC)/QueryParser.g`"   
else
TOOLPATH=$(BUILD_ROOT)/$(SNAP)/$(SITE)/yapps/yapps2.py
GRAMMAR_PATH=$(SRC)/QueryParser.g
endif

MANIFEST_PATH=$(SNAP)/$(SITE)
MANIFEST=$(MANIFEST_PATH)/QueryParser.py

SRC=$(QP)

build: $(PYTHON) $(SRC)/QueryParser.g
	$(PYTHON) $(TOOLPATH) $(GRAMMAR_PATH)
	mkdir -p $(MANIFEST_PATH)
	cp -p QueryParser.py $(BUILD_ROOT)/$(MANIFEST_PATH)

snap: 
	cd $(BUILD_ROOT); \
	tar -cvzf $(QP)/QueryParser-$(SNAP)-$(RELVER).tar.gz $(MANIFEST)
	$(MD5) $(QP)/QueryParser-$(SNAP)-$(RELVER).tar.gz > $(QP)/QueryParser-$(SNAP)-$(RELVER).tar.gz.md5

clean:
	rm -f $(SRC)/QueryParser.py $(MANIFEST)

realclean: clean
	rm -f QueryParser-debug-*.tar.gz* QueryParser-release-*.tar.gz*

install:
	tar -C $(BUILD_ROOT) -cf - $(MANIFEST) | tar -C $(CHANDLERBIN) -xvf -

upload: QueryParser-$(SNAP)-$(RELVER).tar.gz
	scp QueryParser-$(SNAP)-$(RELVER).tar.gz $(UPLOAD)
	scp QueryParser-$(SNAP)-$(RELVER).tar.gz.md5 $(UPLOAD)


