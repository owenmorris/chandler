
include ../Makefile.inc

RELVER=0.1-1
QP=$(INTERNAL)/queryparser

ifeq ($(OS),Cygwin)
TOOLPATH="`cygpath -aw $(BUILD_ROOT)/$(SNAP)/$(SITE)/yapps2.py`"
GRAMMAR_PATH="`cygpath -aw $(SRC)/QueryParser.g`"
else
TOOLPATH=$(BUILD_ROOT)/$(SNAP)/$(SITE)/yapps2.py
GRAMMAR_PATH=$(SRC)/QueryParser.g
endif

SRC=$(QP)

MANIFEST=$(SNAP)/$(SITE)/QueryParser.py

build: $(PYTHON) $(SRC)/QueryParser.g
	$(PYTHON) $(TOOLPATH) $(GRAMMAR_PATH) 
	cp QueryParser.py $(BUILD_ROOT)/$(SNAP)/$(SITE)/

snap: 
	cd $(BUILD_ROOT); \
	tar -cvzf $(QP)/QueryParser-$(SNAP)-$(RELVER).tar.gz \
			 $(MANIFEST)

clean:
	rm -f $(SRC)/QueryParser.py $(MANIFEST)

install:
	cd $(BUILD_ROOT); \
        tar -cf - $(MANIFEST) | tar -C $(BUILD_ROOT)/../chandler -xvf -
