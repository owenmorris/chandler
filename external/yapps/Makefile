
VERSION=2.1.1
YAPPS=$(BUILD_ROOT)/yapps
SRC=$(YAPPS)/yapps3

include $(BUILD_ROOT)/Makefile.inc

BUILD=build_$(SNAP)

build: 
	cd $(SRC); \
	cp yapps2.py yappsrt.py grammar.py parsetree.py $(BUILD_ROOT)/$(SNAP)/$(SITE)/

expand: 
	unzip -o yapps$(VERSION).zip

snap: 
	cd $(BUILD_ROOT); \
	tar -cvzf $(YAPPS)/$(SNAP).tar.gz \
			  $(SNAP)/$(SITE)/yapps2.py \
			  $(SNAP)/$(SITE)/yappsrt.py \
			  $(SNAP)/$(SITE)/grammar.py \
			  $(SNAP)/$(SITE)/parsetree.py

clean:
	rm -rf  $(SRC)/$(BUILD)

