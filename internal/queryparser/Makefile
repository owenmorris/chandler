
include ../Makefile.inc

RELVER=0.1-2
QP=$(INTERNAL)/queryparser

ifeq ($(OS),Cygwin)
TOOLPATH="`cygpath -aw $(BUILD_ROOT)/$(SNAP)/$(SITE)/yapps/yapps2.py`"
GRAMMAR_PATH="`cygpath -aw $(SRC)/QueryParser.g`"
else
TOOLPATH=$(BUILD_ROOT)/$(SNAP)/$(SITE)/yapps/yapps2.py
GRAMMAR_PATH=$(SRC)/QueryParser.g
endif

SRC=$(QP)

MANIFEST=repository/query/parser/QueryParser.py

build: $(PYTHON) $(SRC)/QueryParser.g
	$(PYTHON) $(TOOLPATH) $(GRAMMAR_PATH)
	mkdir -p repository/query/parser
	cp -p QueryParser.py repository/query/parser

snap: 
	tar -cvzf $(QP)/QueryParser-$(SNAP)-$(RELVER).tar.gz $(MANIFEST)

clean:
	rm -f $(SRC)/QueryParser.py $(MANIFEST)

install:
	tar -cf - $(MANIFEST) | tar -C $(CHANDLERHOME) -xvf -

upload: QueryParser-$(SNAP)-$(RELVER).tar.gz
	scp QueryParser-$(SNAP)-$(RELVER).tar.gz $(UPLOAD)


