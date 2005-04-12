
include ../Makefile.inc

RELVER=0.4-4
QP=$(INTERNAL)/queryparser

ifeq ($(OS),Cygwin)
TOOLPATH="`cygpath -aw $(BUILD_ROOT)/$(SNAP)/$(SITE)/yapps/yapps2.py`"
GRAMMAR_PATH="`cygpath -aw $(SRC)/QueryParser.g`"   
MANIFEST_PATH="`cygpath -aw $(SNAP)/$(SITE)`"
MANIFEST="`cygpath -aw $(MANIFEST_PATH)/QueryParser.py`"
else
TOOLPATH=$(BUILD_ROOT)/$(SNAP)/$(SITE)/yapps/yapps2.py
GRAMMAR_PATH=$(SRC)/QueryParser.g
MANIFEST_PATH=$(SNAP)/$(SITE)
MANIFEST=$(MANIFEST_PATH)/QueryParser.py
endif

SRC=$(QP)

build: $(PYTHON) $(SRC)/QueryParser.g
	$(PYTHON) $(TOOLPATH) $(GRAMMAR_PATH)
	mkdir -p $(MANIFEST_PATH)
	cp -p QueryParser.py $(MANIFEST_PATH)

snap: 
	tar -cvzf $(QP)/QueryParser-$(SNAP)-$(RELVER).tar.gz $(MANIFEST)
	$(MD5) QueryParser-$(SNAP)-$(RELVER).tar.gz > QueryParser-$(SNAP)-$(RELVER).tar.gz.md5

clean:
	rm -f $(SRC)/QueryParser.py $(MANIFEST_PATH)

realclean: clean
	rm -f QueryParser-debug-*.tar.gz* QueryParser-release-*.tar.gz*

install:
	tar -cf - $(MANIFEST) | tar -C $(CHANDLERBIN) -xvf -

upload: QueryParser-$(SNAP)-$(RELVER).tar.gz
	scp QueryParser-$(SNAP)-$(RELVER).tar.gz $(UPLOAD)
	scp QueryParser-$(SNAP)-$(RELVER).tar.gz.md5 $(UPLOAD)


