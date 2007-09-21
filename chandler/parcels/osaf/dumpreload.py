#   Copyright (c) 2003-2007 Open Source Applications Foundation
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.


"""Dump and Reload module"""

import logging, cPickle, sys, os, wx
from osaf import sharing
from osaf.sharing.eim import uri_registry, RecordClass
from application import schema
from osaf.framework import password, MasterPassword
from osaf.framework.twisted import waitForDeferred
from i18n import ChandlerMessageFactory as _
from osaf.activity import ActivityAborted
from pkg_resources import iter_entry_points

logger = logging.getLogger(__name__)

class UnknownRecord(object):
    """Class representing an unknown record type"""
    def __init__(self, *args):
        self.data = args
        
    
class PickleSerializer(object):
    """ Serializes to a byte-length string, followed by newline, followed by
        a pickle string of the specified length """

    @classmethod
    def dumps(cls, ob):
        from cStringIO import StringIO
        s = StringIO()
        cls.dumper(s)(ob)
        return s.getvalue()

    @classmethod
    def loads(cls, s):
        from cStringIO import StringIO
        return cls.loader(StringIO(s))()
        
    @classmethod
    def dumper(cls, output):
        pickler = cPickle.Pickler(output, 2)
        pickler.persistent_id = cls.persistent_id
        return pickler.dump

    @classmethod
    def loader(cls, input):
        unpickler = cPickle.Unpickler(input)
        unpickler.persistent_load = cls.persistent_load
        return unpickler.load

    @staticmethod
    def persistent_id(ob):
        if isinstance(ob, RecordClass):
            # save record classes by URI *and* module
            return ob.URI, ob.__module__   

    @staticmethod
    def persistent_load((uri, module)):
        try:
            return uri_registry[uri]
        except KeyError:
            pass
        # It wasn't in the registry by URI, see if we can import it
        if module not in sys.modules:
            try:
                schema.importString(module)
            except ImportError:
                pass
        try:
            # Maybe it's in the registry now...
            return uri_registry[uri]
        except KeyError:
            # Create a dummy record type for the object
            # XXX this really should try some sort of persistent registry
            #     before falling back to a fake record type
            #
            rtype = type("Unknown", (UnknownRecord,), dict(URI=uri))
            uri_registry[uri] = rtype
            return rtype


def dump(rv, filename, uuids=None, serializer=PickleSerializer,
    activity=None, obfuscate=False):
    """
    Dumps EIM records to a file, file permissions 0600.
    """

    translator = getTranslator()


    trans = translator(rv)
    trans.obfuscation = obfuscate

    aliases = list()

    if uuids:
        for uuid in uuids:
            aliases.append(trans.getAliasForItem(rv.findUUID(uuid)))
    else:
        for item in schema.Item.iterItems(rv):
            if not str(item.itsPath).startswith("//parcels"):
                aliases.append(trans.getAliasForItem(item))

    # Sort on alias so masters are dumped before occurrences
    aliases.sort()

    trans.startExport()

    try:
        flags = os.O_EXCL | os.O_CREAT | os.O_WRONLY | os.O_BINARY
    except AttributeError:
        flags = os.O_EXCL | os.O_CREAT | os.O_WRONLY

    try:
        # Need to remove the file, otherwise we'll use existing permissions
        os.remove(filename)
    except OSError:
        pass
    # XXX This will fail if someone created the file after the remove but
    # XXX before we got here, so the caller should be prepared to handle that.
    output = os.fdopen(os.open(filename, flags, 0600), 'wb')
    try:
        dump = serializer.dumper(output)

        if activity:
            count = len(aliases)
            activity.update(msg="Dumping %d records" % count, totalWork=count)

        i = 0
        for alias in aliases:
            uuid = trans.getUUIDForAlias(alias)
            item = rv.findUUID(uuid)
            for record in trans.exportItem(item):
                dump(record)
            i += 1
            if activity:
                activity.update(msg="Dumped %d of %d items" % (i, count),
                    work=1)

        if activity:
            activity.update(totalWork=None) # we don't know upcoming total work

        for record in trans.finishExport():
            if activity:
                count += 1
                activity.update(msg="Dumping additional record")

            dump(record)

        dump(None)
        del dump
    except ActivityAborted:
        os.remove(filename)
    finally:
        output.close()

    if activity:
        activity.update(msg="Dumped %d records" % count)



def reload(rv, filename, serializer=PickleSerializer, activity=None,
    testmode=False):
    """ Loads EIM records from a file and applies them """

    translator = getTranslator()

    if not testmode:
        oldMaster = waitForDeferred(MasterPassword.get(rv))
    else:
        oldMaster = ''
        newMaster = 'secret'

    if activity:
        activity.update(totalWork=None, msg=_("Counting records..."))
        input = open(filename, "rb")
        load = serializer.loader(input)
        i = 0
        while True:
            record = load()
            if not record:
                break
            i += 1
        input.close()
        activity.update(totalWork=i)


    trans = translator(rv)
    trans.startImport()

    input = open(filename, "rb")
    try:
        load = serializer.loader(input)
        i = 0
        while True:
            record = load()
            if not record:
                break
            trans.importRecord(record)
            i += 1
            if activity:
                activity.update(msg="Imported %d records" % i, work=1)
            if i % 1000 == 0: # Commit every 1,000 records
                if activity:
                    activity.update(msg="Saving...")
                rv.commit()

        del load
    finally:
        input.close()

    trans.finishImport()

    if activity:
        activity.update(msg="Saving...")
    rv.commit()


    # Passwords that existed before reload are encrypted with oldMaster, and
    # passwords that we reloaded are encrypted with newMaster, so now we need
    # to go through all passwords and re-encrypt all the old ones with
    # newMaster.
    
    # First, let's get the newMaster
    waitForDeferred(MasterPassword.clear())
    if not testmode:
        prefs = schema.ns("osaf.framework.MasterPassword",
                          rv).masterPasswordPrefs
        if prefs.masterPassword:
            wx.MessageBox (_(u'You will need to supply the master password that was used to protect the account passwords in the file.'),
                           _(u'Protect Passwords'),
                           parent=wx.GetApp().mainFrame)
        
        dummy = schema.ns("osaf.framework.password",
                          rv).passwordPrefs.dummyPassword

        while True:
            try:
                newMaster = waitForDeferred(MasterPassword.get(rv, testPassword=dummy))
                break
            except password.NoMasterPassword:
                if wx.MessageBox(_(u'If you do not supply the master password, all passwords will be reset. Reset?'),
                                 _(u'Reset Master Password?'),
                                 style = wx.YES_NO,
                                 parent=wx.GetApp().mainFrame) == wx.YES:
                    MasterPassword.reset(rv)
                    return
    
    # Then re-encrypt
    for item in password.Password.iterItems(rv):
        if not waitForDeferred(item.initialized()):
            # Don't need to re-encrypt uninitialized passwords
            continue
        
        try:
            pw = waitForDeferred(item.decryptPassword(masterPassword=oldMaster))
        except password.DecryptionError:
            # Maybe this was one of the new passwords loaded from
            # dump, so let's try the new master password
            try:
                waitForDeferred(item.decryptPassword(masterPassword=newMaster))
            except password.DecryptionError:
                # Oops, we are in trouble, can't really do much but
                # reset() to avoid further problems.
                logger.exception('found passwords that could not be decrypted; clearing passwords')
                MasterPassword.reset(rv)
                break
            # Since this is already encrypted with the new
            # master password we don't need to re-encrypt
            continue

        waitForDeferred(item.encryptPassword(pw, masterPassword=newMaster))


def convertToTextFile(fromPath, toPath, serializer=PickleSerializer,
    activity=None):

    if activity:
        activity.update(totalWork=None, msg=_("Counting records..."))
        input = open(fromPath, "rb")
        load = serializer.loader(input)
        i = 0
        while True:
            record = load()
            if not record:
                break
            i += 1
        input.close()
        activity.update(totalWork=i)


    input = open(fromPath, "rb")
    output = open(toPath, "wb")
    try:
        load = serializer.loader(input)
        i = 0
        while True:
            record = load()
            if not record:
                break
            output.write(str(record))
            output.write("\n\n")
            i += 1
            if activity:
                activity.update(msg="Converted %d records" % i, work=1)

        del load
    finally:
        input.close()
        output.close()





translator = None

def getTranslator():
    global translator

    if translator is not None:
        return translator

    mixins = [ep.load() for ep in iter_entry_points('chandler.chex_mixins')]
    if not mixins:
        translator = sharing.DumpTranslator
    else:
        mixins.insert(0, sharing.DumpTranslator)
        translator = type("Translator", tuple(mixins),
            {
                'version'     : 1,
                'URI'         : ' '.join(m.URI for m in mixins),
                'description' : u'Mixed-in translator'
            }
        )
    return translator
