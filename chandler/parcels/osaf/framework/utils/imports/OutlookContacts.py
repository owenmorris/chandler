"""Import contacts exported by Outlook to CSV format."""

__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import application.Globals as Globals
import CSVImporter
import os
import mx.DateTime as DateTime

"""
    Explanation for the mapping constant: @@@TODO
"""

TOP=1
DATETYPE=2
LISTTYPE=3
CONCATTYPE=4
CONDITIONALCONST=5

TRANSLATIONMAP=\
  (TOP, "//parcels/OSAF/contentmodel/contacts/Contact", 
      {"contactName" : 
          {"firstName" : "First Name",
           "lastName" : "Last Name",
           "middleName" : "Middle Name"},
       "birthday" : (DATETYPE, "Birthday"),
       "homeSection" :
          {"spouse" : "Spouse",
           "children" : (LISTTYPE, "Children"),
           "webPages" : (LISTTYPE, "Web Page"),
           "anniversary" : (DATETYPE, "Anniversary"),
           "emailAddresses" : (LISTTYPE,
              {"emailAddress" : "E-mail Address"},
              {"emailAddress" : "E-mail 2 Address"},
              {"emailAddress" : "E-mail 3 Address"}),
           "streetAddresses" : (LISTTYPE,
              {"streetAddress" : (CONCATTYPE, 
                   "Home Street",
                   "Home Street 2",
                   "Home Street 3"),
               "locality" : "Home City",
               "region" : "Home State",
               "postalCode" : "Home Postal Code",
               "countryName" : "Home Country",
               "postOfficeBox" : "PO Box"}),
           "phoneNumbers" : (LISTTYPE,
              {"phoneNumber" : "Home Phone",
               "phoneType" :
                   (LISTTYPE, (CONDITIONALCONST, "voice", "Home Phone"))},
              {"phoneNumber" : "Home Phone 2",
               "phoneType" : 
                   (LISTTYPE, (CONDITIONALCONST, "voice", "Home Phone 2"))},
              {"phoneNumber" : "ISDN",
               "phoneType" : 
                   (LISTTYPE, (CONDITIONALCONST, "isdn", "ISDN"))},
              {"phoneNumber" : "Mobile Phone",
               "phoneType" : 
                   (LISTTYPE, (CONDITIONALCONST, "cell", "Mobile Phone"))},
              {"phoneNumber" : "Home Fax",
               "phoneType" : 
                   (LISTTYPE, (CONDITIONALCONST, "fax", "Home Fax"))},
              {"phoneNumber" : "Car Phone",
               "phoneType" : 
                   (LISTTYPE, (CONDITIONALCONST, "car", "Car Phone"))},
              {"phoneNumber" : "Other Phone",
               "phoneType" : 
                   (LISTTYPE, (CONDITIONALCONST, "voice", "Other Phone"))},
              {"phoneNumber" : "Pager",
               "phoneType" : 
                   (LISTTYPE, (CONDITIONALCONST, "pager", "Pager"))},
              {"phoneNumber" : "Primary Phone",
               "phoneType" : 
                   (LISTTYPE, (CONDITIONALCONST, "voice", "Primary Phone"))})},
       "workSection" :
          {"employer" : "Company",
           "jobTitle" : "Job Title",
           "phoneNumbers" : (LISTTYPE,
              {"phoneNumber" : "Business Phone",
               "phoneType" :
                   (LISTTYPE, (CONDITIONALCONST, "voice", "Business Phone"))},
              {"phoneNumber" : "Business Phone 2",
               "phoneType" : 
                   (LISTTYPE, (CONDITIONALCONST, "voice", "Business Phone 2"))},
              {"phoneNumber" : "Business Fax",
               "phoneType" :
                   (LISTTYPE, (CONDITIONALCONST, "fax", "Business Fax"))},
              {"phoneNumber" : "Company Main Phone",
               "phoneType" : 
                   (LISTTYPE, (CONDITIONALCONST,"voice","Company Main Phone"))}),
           "streetAddresses" : (LISTTYPE,
              {"streetAddress" : (CONCATTYPE, 
                   "Business Street",
                   "Business Street 2",
                   "Business Street 3"),
               "locality" : "Business City",
               "region" : "Business State",
               "postalCode" : "Business Postal Code",
               "countryName" : "Business Country"})}})

TRANSLATIONMAP_OLD=\
  (TOP, "//parcels/OSAF/contentmodel/contacts/Contact", 
      {"contactName" : 
          {"firstName" : "First Name",
           "lastName" : "Last Name",
           "middleName" : "Middle Name"},
       "birthday" : (DATETYPE, "Birthday"),
       "homeSection" :
          {"spouse" : "Spouse",
           "children" : (LISTTYPE, "Children"),
           "webPages" : (LISTTYPE, "Web Page"),
           "anniversary" : (DATETYPE, "Anniversary"),
           "emailAddresses" : (LISTTYPE,
              {"emailAddress" : "E-mail Address"},
              {"emailAddress" : "E-mail 2 Address"},
              {"emailAddress" : "E-mail 3 Address"}),
           "streetAddresses" : (LISTTYPE,
              {"streetAddress" : (CONCATTYPE, 
                   "Home Street",
                   "Home Street 2",
                   "Home Street 3"),
               "locality" : "Home City",
               "region" : "Home State",
               "postalCode" : "Home Postal Code",
               "countryName" : "Home Country",
               "postOfficeBox" : "PO Box"}),
           "phoneNumbers" : (LISTTYPE,
              {"phoneNumber" : "Home Phone",
               "phoneType" :
                   (LISTTYPE, (CONDITIONALCONST, "voice", "Home Phone"))},
              {"phoneNumber" : "Home Phone 2",
               "phoneType" : 
                   (LISTTYPE, (CONDITIONALCONST, "voice", "Home Phone 2"))},
              {"phoneNumber" : "ISDN",
               "phoneType" : 
                   (LISTTYPE, (CONDITIONALCONST, "isdn", "ISDN"))},
              {"phoneNumber" : "Mobile Phone",
               "phoneType" : 
                   (LISTTYPE, (CONDITIONALCONST, "cell", "Mobile Phone"))},
              {"phoneNumber" : "Home Fax",
               "phoneType" : 
                   (LISTTYPE, (CONDITIONALCONST, "fax", "Home Fax"))},
              {"phoneNumber" : "Car Phone",
               "phoneType" : 
                   (LISTTYPE, (CONDITIONALCONST, "car", "Car Phone"))},
              {"phoneNumber" : "Other Phone",
               "phoneType" : 
                   (LISTTYPE, (CONDITIONALCONST, "voice", "Other Phone"))},
              {"phoneNumber" : "Pager",
               "phoneType" : 
                   (LISTTYPE, (CONDITIONALCONST, "pager", "Pager"))},
              {"phoneNumber" : "Primary Phone",
               "phoneType" : 
                   (LISTTYPE, (CONDITIONALCONST, "voice", "Primary Phone"))})},
       "workSection" :
          {"employer" : "Company",
           "jobTitle" : "Job Title",
           "phoneNumbers" : (LISTTYPE,
              {"phoneNumber" : "Business Phone",
               "phoneType" :
                   (LISTTYPE, (CONDITIONALCONST, "voice", "Business Phone"))},
              {"phoneNumber" : "Business Phone 2",
               "phoneType" : 
                   (LISTTYPE, (CONDITIONALCONST, "voice", "Business Phone 2"))},
              {"phoneNumber" : "Business Fax",
               "phoneType" :
                   (LISTTYPE, (CONDITIONALCONST, "fax", "Business Fax"))},
              {"phoneNumber" : "Company Main Phone",
               "phoneType" : 
                   (LISTTYPE, (CONDITIONALCONST,"voice","Company Main Phone"))}),
           "streetAddresses" : (LISTTYPE,
              {"streetAddress" : (CONCATTYPE, 
                   "Business Street",
                   "Business Street 2",
                   "Business Street 3"),
               "locality" : "Business City",
               "region" : "Business State",
               "postalCode" : "Business Postal Code",
               "countryName" : "Business Country"})}})



#Something should probably be done with the "Notes" field @@@TODO
#Also deal with the special case of gender (enum){"gender" : "Gender"} @@@TODO

#Why do some aspects not get exposed to python .aspectname access?  Or was this
#just a problem with the phoneType cardinality?
#Delete oddity
#Should all Kinds offer a newItem method?

"""
        Importing Outlook CSV Contacts currently munges data in the following
        ways:
        * Outlook doesn't distinguish between home and work email addresses,
        so if there are multiple email addresses they're arbitrarily mapped
        to the home section.
        * Things like mailing lists don't generally have first-middle-last
        names, but Outlook treats them like they do.  Chandler's Full Name isn't
        currently set.
        * Outlook's E-mail Type (which is mostly just SMTP for non-Microsoft-
        centric users) is ignored.
        * Children is treated as a single string, not parsed into multiple kids
        * E-mail Display Name is ignored.
        * Title (Mr., Dr., etc.) is ignored. 
        * Suffix is ignored.
        * "Other" (beyond home and work) addresses are ignored.
        * See the list below for a complete list of fields that are ignored

currently ignored fields:

"Title" "Suffix"	"Department"
"Other Street"	"Other Street 2"  "Other Street 3"	"Other City" "Other State"
"Other Postal Code"   "Other Country"   "Assistant's Phone"   "Assistant's Name"
"Telex"   "TTY/TDD Phone"   "Radio Phone" "Callback"					
"Account" "Billing Information" "Categories"	"Directory Server"
"E-mail Type"	"E-mail Display Name"	"E-mail 2 Type"	
"E-mail 2 Display Name"	"E-mail 3 Type"	"E-mail 3 Display Name"
"Government ID Number"	"Hobby"	"Initials"	"Internet Free Busy"
"Keywords"	"Language"	"Location"	"Manager's Name"	"Mileage"
"Office Location"	"Organizational ID Number"    "Priority"	"Private"
"Profession"	"Referred By"	"Sensitivity"	"User 1"	"User 2"
"User 3"	"User 4"
"""

class OutlookContacts(CSVImporter.CSVImporter):
    """Import contacts exported by Outlook to CSV format."""
    def __init__(self, sourceFile=None, version="2000"):
        """Currently version is ignored, assumes Outlook 2000 format."""
        CSVImporter.CSVImporter.__init__(self)        
        if sourceFile is None:
            #hack to avoid user interface to input a file, os.getcwd()
            #will probably be the Chandler dir, but YMMV.
            self.setSourcePath(os.path.join(os.getcwd(), "contacts.csv"))
        else:
            self.setSourcePath(sourceFile)

    def createAttributes(self, parent, tree, importRowDict, kind):
        """Populate parent's attributes.
        
        tree should be a dictionary whose keys are itemNames
        of attributes of parent.  Attributes of the appropriate Kind are created
        for each key, then are populated by recursively calling processBranch.
        
        """
        nonempty=False
        if kind is None:
            item=parent
        else:
            item=kind.newItem(None, parent)
        for key in tree:
            childData=tree[key]
            childKind=item.getAttributeAspect(key, "type")
            value=self.processBranch(item, childData, importRowDict, childKind)
            if value is not None:
                item.setAttributeValue(key, value)
                nonempty=True
        if nonempty:
            return item
        else:
            if kind is not None:
                item.delete()
            return None
            
    def createString(self, parent, tree, importRowDict):
        """Return importRowDict[tree]."""
        
        if not importRowDict[tree]:
            return None
        else:
            return importRowDict[tree]

    def createTop(self, parent, tree, importRowDict):
        """Create the main Kind for this object."""
        topKind=Globals.repository.find(tree[0])
        top=topKind.newItem(None, parent)
        return self.processBranch(top, tree[1], importRowDict)

    def createDate(self, datekey, importRowDict):
        """Create a RelativeDateTime for importRowDict[datekey].
        
        Based on Outlook 2000's export to CSV format for dates.  Dates are of
        the form "m/d/y", empty dates are expressed as "0/0/00".
                
        """
        
        dateString=importRowDict[datekey]
        if dateString in ["0/0/00", ""]:
            return None
        else:
            dateTime= DateTime.Parser.DateTimeFromString(\
                                          dateString, ('us', 'unknown'))
            isoString=DateTime.ISO.str(dateTime)
            return DateTime.Parser.RelativeDateTimeFromString(isoString)

    def createList(self, parent, tree, importRowDict, kind):
        """Create a list of Items, one for each non-empty element of tree."""
        returnList = []
        try:
            #String and DateTime Kinds don't offer a newItem method
            item=kind.newItem(None, parent.getItemParent())
        except AttributeError:
            item=None
        for branch in tree:
            value=self.processBranch(item, branch, importRowDict)
            if value is not None:
                returnList.append(value)
                if item is not None:
                    item=kind.newItem(None, parent.getItemParent())
        if item is not None:
            #if item was ever set, we'll have an extra item
            item.delete()
        if len(returnList) == 0:
            return None
        else:
            return returnList

    def createConcatString(self, keylist, importRowDict):
        """Concatenate values in importRowDict from keylist's keys."""
        valueList=[importRowDict[key] for key in keylist]
        lines=os.linesep.join(valueList)
        if lines.strip() == "":
            return None
        else:
            return lines
        
    def createCondConst(self, const, keylist, importRowDict):
        """Return const if any items referred to by keylist are nonempty."""
        if filter(None, [importRowDict[key] for key in keylist]):
            return const
        else:
            return None
        
    def processBranch(self, parent, tree, importRowDict, kind=None):
        """Process a leaf of the translation struct.
        
        tree should be a string, a dictionary, or a tuple whose
        first element is one of the translation constants.  Create a new Item
        of the appropriate Kind and parent using tree's type to
        determine the appropriate creation method.  Recurse through the
        tree.
        
        Creation methods should return None if the relevant fields in 
        importRowDict are empty (empty may differ for different field types and
        different import formats, for instance Outlook exports empty dates as
        0/0/00, whereas string formats should return None if they're empty
        or contain only whitespace.
        
        """
        if type(tree)==dict:
            return self.createAttributes(parent, tree, importRowDict, kind)
        elif type(tree) in [str, unicode]:
            return self.createString(parent, tree, importRowDict)
        elif type(tree)==tuple:
            if   tree[0]==TOP:
                return self.createTop(parent, tree[1:], importRowDict)
            elif tree[0]==DATETYPE:
                return self.createDate(tree[1], importRowDict)
            elif tree[0]==LISTTYPE:
                return self.createList(parent, tree[1:], importRowDict, kind)
            elif tree[0]==CONDITIONALCONST:
                return self.createCondConst(tree[1], tree[2:], importRowDict)
            elif tree[0]==CONCATTYPE:
                return self.createConcatString(tree[1:], importRowDict)
            else:
                raise Importer.CreationError, \
                 ("Can't process tree, constant not recognized",\
                 self.lineNumber)
        else:
            raise Importer.CreationError, \
             ("Can't process tree, type not recognized", self.lineNumber)

    def createObjectFromDict(self, importRowDict):
        """Create a Contact object and populate it from the given dict."""
        i=self.processBranch(self.getDestination(),TRANSLATIONMAP,importRowDict)
        return i

    def massageObject(self, object):
        """Deal with registering homeSection and workSection after the fact."""
        kindPath="//parcels/OSAF/contentmodel/contacts/ContactSection"
        sectionKind=Globals.repository.find(kindPath)
        sectionsList=[]
        for child in object.iterChildren():
            if child.kind is sectionKind:
                sectionsList.append(child)
        object.sections=sectionsList
        
TEST=\
{'Account': '',
 'Anniversary': '2/12/2004',
 "Assistant's Name": '',
 "Assistant's Phone": '',
 'Billing Information': '',
 'Birthday': '5/12/1977',
 'Business City': '',
 'Business Country': '',
 'Business Fax': '',
 'Business Phone': '',
 'Business Phone 2': '',
 'Business Postal Code': '',
 'Business State': '',
 'Business Street': '',
 'Business Street 2': '',
 'Business Street 3': '',
 'Callback': '',
 'Car Phone': '',
 'Categories': '',
 'Children': '',
 'Company': 'MyCompany',
 'Company Main Phone': '',
 'Department': '',
 'Directory Server': '',
 'E-mail 2 Address': '',
 'E-mail 2 Display Name': '',
 'E-mail 2 Type': '',
 'E-mail 3 Address': '',
 'E-mail 3 Display Name': '',
 'E-mail 3 Type': '',
 'E-mail Address': 'jeffrey@skyhouseconsulting.com',
 'E-mail Display Name': 'jeffrey@skyhouseconsulting.com',
 'E-mail Type': 'SMTP',
 'First Name': 'Jeffrey',
 'Gender': 'Male',
 'Government ID Number': '',
 'Hobby': '',
 'Home City': '',
 'Home Country': '',
 'Home Fax': '',
 'Home Phone': '660-883-5881',
 'Home Phone 2': '',
 'Home Postal Code': '',
 'Home State': '',
 'Home Street': '',
 'Home Street 2': '',
 'Home Street 3': '',
 'ISDN': '',
 'Initials': '',
 'Internet Free Busy': '',
 'Job Title': 'Programmer',
 'Keywords': '',
 'Language': '',
 'Last Name': 'Harris',
 'Location': '',
 "Manager's Name": '',
 'Middle Name': '',
 'Mileage': '',
 'Mobile Phone': '',
 'Notes': '',
 'Office Location': '',
 'Organizational ID Number': '',
 'Other City': '',
 'Other Country': '',
 'Other Fax': '',
 'Other Phone': '',
 'Other Postal Code': '',
 'Other State': '',
 'Other Street': '',
 'Other Street 2': '',
 'Other Street 3': '',
 'PO Box': '',
 'Pager': '',
 'Primary Phone': '',
 'Priority': 'Low',
 'Private': '',
 'Profession': '',
 'Radio Phone': '',
 'Referred By': '',
 'Sensitivity': 'Normal',
 'Spouse': '',
 'Suffix': '',
 'TTY/TDD Phone': '',
 'Telex': '',
 'Title': '',
 'User 1': '',
 'User 2': '',
 'User 3': '',
 'User 4': '',
 'Web Page': ''}