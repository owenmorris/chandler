"""Import contacts exported by Outlook to CSV format."""

__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import Importer, MapXML, os

#@@@TODO deal with the special case of gender (enum){"gender" : "Gender"}
#Unspecified in Outlook, Unknown in Chandler

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
        * Suffix is ignored.
        * "Other" (beyond home and work) addresses are ignored.
        * See the list below for a complete list of fields that are ignored
        * Gender isn't currently dealt with because enumeration mappings haven't
        been implemented.

currently ignored fields:

"Title" => not the same as jobTitle, things like "Prof.",  needed
"Suffix" => needed
"Department" => needed
"Profession" => needed
* Do other.
"Other Street"        "Other Street 2"  "Other Street 3"        "Other City" "Other State"
"Other Postal Code"   "Other Country"
"Assistant's Phone"   "Assistant's Name" => Assistant needed?
"Manager's Name" => Manager needed?
"Telex"   "TTY/TDD Phone"   "Radio Phone" "Callback" => what IS this?
"Initials" => is initials entirely a derived field? can it just be ignored?                       

"Categories" => semi-colon separated list of categories, some defined by Outlook, some by the user

"Account" "Billing Information"
"Directory Server" => NetMeeting server for the contact
"E-mail Type" => SMTP or FAX or MSN or MSNINET, ignore "E-mail 2 Type" "E-mail 3 Type"  
"E-mail Display Name" => ignore? "E-mail 2 Display Name" "E-mail 3 Display Name"
"Government ID Number" "Organizational ID Number" => ?
"Hobby" => ?
"Internet Free Busy" => iCalendar server, probably should be used.
"Keywords" => not exported, but in Outlook look identical to Categories, ignore
"Language"
"Location"
"Office Location" 
"Mileage" => Exists by default for all Outlook items, probably can be ignored
"Priority" "Private"
"Referred By"
"Sensitivity"
"User 1"        "User 2" "User 3"        "User 4"
"""

MAPPINGDIR="parcels/osaf/framework/utils/imports"

class OutlookContacts(Importer.CSVImporter):
    """Import contacts exported by Outlook to CSV format."""
    def __init__(self, view, sourceFile=None, mapping="outlook2000.xml"):
        """Currently version is ignored, assumes Outlook 2000 format."""
        super(OutlookContacts, self).__init__(view)
        if sourceFile is None:
            #hack to avoid user interface to input a file, os.getcwd()
            #will probably be the Chandler dir, but YMMV.
            self.source=(os.path.join(os.getcwd(), "contacts.csv"))
        else:
            self.source=(sourceFile)
        path=os.path.join(MAPPINGDIR, mapping)
        reader=MapXML.MapXML(path)
        self.mapping=reader.streamFile()

    def postProcess(self, view, object):
        """Deal with registering homeSection and workSection after the fact."""
        kindPath="//parcels/osaf/contentmodel/contacts/ContactSection"
        sectionKind=view.findPath(kindPath)
        sectionsList=[]
        for child in object.iterChildren():
            if child.itsKind is sectionKind:
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
