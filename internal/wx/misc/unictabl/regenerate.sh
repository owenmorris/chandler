#!/bin/sh
# CVS-ID: $Id: regenerate.sh 5166 2005-04-29 01:36:53Z davids $

echo ""
echo "-----------------------------------"
echo " Refreshing tables, please wait..."
echo "-----------------------------------"
echo ""

sh ./mk_fallbacks.sh
sh ./mk_encodings.sh

echo "  * removing temporary files..."

rm -f Fallbacks UnicodeChars

echo "
  * copying tables to src/common/unictabl.inc..."
  
mv -f unictabl.inc ../../src/common/unictabl.inc

echo "
  DONE
"
