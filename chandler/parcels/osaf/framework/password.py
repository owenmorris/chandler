#   Copyright (c) 2007 Open Source Applications Foundation
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

__all__ = [
    'PasswordError',
    'DecryptionError',
    'EncryptionError',
    'NoMasterPassword',
    'Password',
]

# XXX EIM for Password stuff

# XXX test all scenarios with timeout of 0 second with non-default pw and answer correctly
# XXX same but cancel dialog; ensure we deal with exception correctly

import os, hmac, string, cStringIO
from hashlib import sha256
from M2Crypto import EVP
from i18n import ChandlerMessageFactory as _
from application import schema
from osaf import Preferences
from osaf.framework.twisted import runInUIThread, waitForDeferred
from osaf.framework import MasterPassword


class PasswordError(Exception):
    """
    Abstract base class for password specific errors.
    """

class NoMasterPassword(PasswordError):
    """
    This exception will be raised if the code requests the master password
    and the user cancels from the request to enter it.

    The string value should be a localized message.
    """

class DecryptionError(PasswordError):
    """
    Failed to decrypt password. Can be raised if the user enters incorrect
    master password, for example.
    """

class EncryptionError(PasswordError):
    """
    Failed to encrypt password
    """
    
class PasswordTooLong(PasswordError):
    """
    The password is too long
    """


class Password(schema.Item):
    """
    Secure password storage.
    
    @warning: Once master password is in memory, it will be possible
              to get the encrypted passwords as well. This may be possible
              even after the master password has timed out and cleared.
    @warning: If the password is used, it will be decrypted and available
              in plain text in memory, possibly even after it has been
              explicitly cleared after use.
    @warning: If weak master passwords (like empty) are used, the
              encryption will not be of much help.
    """
    ciphertext = schema.One(
        schema.Bytes,
        doc = 'The encrypted password',
    )
    iv = schema.One(
        schema.Bytes,
        doc = 'IV to be used when encrypting/decrypting password',
    )
    salt = schema.One(
        schema.Bytes,
        doc = 'Salt to be used when deriving key from master password',
    )

    holders = schema.Sequence() # inverse=password.holders

    @runInUIThread
    def decryptPassword(self, masterPassword=None, window=None):
        """
        Decrypt password and return it.
        
        @raise NoMasterPassword: NoMasterPassword will be raised if 
                                 masterPassword parameter is None and we have a
                                 non-default master password that has timed out,
                                 and the user cancels the dialog where we ask for
                                 it.

        @raise PasswordTooLong:  Password is too long.

        @return: Return password.
        @rtype:  unicode
        """
        try:
            if not self.ciphertext or not self.iv or not self.salt:
                return u''
        except AttributeError:
            # We can determine the correct master password by iterating over
            # passwords, decrypting them, and getting at least one non-empty
            # password.
            return u''
        
        if len(self.ciphertext) > 1024:
            waitForDeferred(self.clear())
            raise PasswordTooLong(_(u'Password is too long'))
        
        if masterPassword is None:
            masterPassword = waitForDeferred(MasterPassword.get(self.itsView, window))
        
        # the crypto algorithms are unicode unfriendly
        if isinstance(masterPassword, unicode):
            masterPassword = masterPassword.encode('utf8')

        # derive 256 bit key using the pbkdf2 standard
        key = EVP.pbkdf2(masterPassword, self.salt, iter=1000, keylen=32)

        # Derive encryption key and HMAC key from it
        # See Practical Cryptography section 8.4.1.
        hmacKey = sha256(key + 'MAC').digest()
        encKey = sha256(key + 'encrypt').digest()
        del key
        
        # decrypt
        ret = decrypt(self.ciphertext, encKey, self.iv)
        del encKey
        
        # Check MAC
        mac = ret[-64:]
        ret = ret[:-64]
        try:
            if hmac.new(hmacKey, ret + self.iv + self.salt,
                        sha256).hexdigest() != mac:
                raise DecryptionError('HMAC does not match')
        finally:
            del hmacKey

        return unicode(ret, 'utf8')

    @runInUIThread
    def encryptPassword(self, password, masterPassword=None, window=None):
        """
        Encrypt and store password.
        
        @raise NoMasterPassword: NoMasterPassword will be raised if 
                                 masterPassword parameter is None and we have a
                                 non-default master password that has timed out,
                                 and the user cancels the dialog where we ask for
                                 it.

        @raise PasswordTooLong:  Password is too long.

        @param password: The password to store
        @type param:     str or unicode
        """
        if masterPassword is None:
            masterPassword = waitForDeferred(MasterPassword.get(self.itsView, window))
            
        # the crypto algorithms are unicode unfriendly
        if isinstance(password, unicode):
            password = password.encode('utf8')
        if isinstance(masterPassword, unicode):
            masterPassword = masterPassword.encode('utf8')
        
        # get 256 bit random encryption salt
        self.salt = os.urandom(32)
        # derive 256 bit encryption key using the pbkdf2 standard
        key = EVP.pbkdf2(masterPassword, self.salt, iter=1000, keylen=32)
        
        # Derive encryption key and HMAC key from it
        # See Practical Cryptography section 8.4.1.
        hmacKey = sha256(key + 'MAC').digest()
        encKey = sha256(key + 'encrypt').digest()
        del key

        # get 256 bit random iv
        self.iv = os.urandom(32)

        # Add HMAC to password so that we can check during decrypt if we got
        # the right password back. We are doing sign-then-encrypt, which let's
        # us encrypt empty passwords (otherwise we'd need to pad with some
        # string to encrypt). Practical Cryptography by Schneier & Ferguson
        # also recommends doing it in this order in section 8.2.
        mac = hmac.new(hmacKey,
                       password + self.iv + self.salt,
                       sha256).hexdigest()
        del hmacKey

        # encrypt using AES (Rijndael)
        self.ciphertext = encrypt(password + mac, encKey, self.iv)

        if len(self.ciphertext) > 1024:
            waitForDeferred(self.clear())
            raise PasswordTooLong(_(u'Password is too long'))
        

    @runInUIThread
    def clear(self):
        try:
            del self.ciphertext
        except AttributeError:
            pass
        try:
            del self.iv
        except AttributeError:
            pass
        try:
            del self.salt
        except AttributeError:
            pass
        
    @runInUIThread
    def initialized(self):
        try:
            if not self.ciphertext or not self.iv or not self.salt:
                return False
        except AttributeError:
            return False
        
        return True
    
    @runInUIThread
    def recordTuple(self):
        try:
            if not self.ciphertext or not self.iv or not self.salt:
                return '', '', ''
        except AttributeError:
            return '', '', ''

        return self.ciphertext, self.iv, self.salt


# Common attribute for password holders. All kinds referencing it better use
# the same name for their attribute, currently 'password'.
passwordAttribute = schema.One(
    Password,
    inverse=Password.holders
)


def _cipherFilter(cipher, inf, outf):
    # decrypt/encrypt helper
    while 1:
        buf = inf.read()
        if not buf:
            break
        outf.write(cipher.update(buf))
    outf.write(cipher.final())
    return outf.getvalue()


def decrypt(ciphertext, key, iv, alg='aes_256_cbc'):
    """
    Decrypt ciphertext
    """
    assert len(key) == len(iv) == 32
    cipher = EVP.Cipher(alg=alg, key=key, iv=iv, op=0)
    del key
    pbuf = cStringIO.StringIO()
    cbuf = cStringIO.StringIO(ciphertext)
    plaintext = _cipherFilter(cipher, cbuf, pbuf)
    pbuf.close()
    cbuf.close()
    return plaintext


def encrypt(plaintext, key, iv, alg='aes_256_cbc'):
    """
    Encrypt plaintext
    """
    assert len(key) == len(iv) == 32
    cipher = EVP.Cipher(alg=alg, key=key, iv=iv, op=1)
    del key
    pbuf = cStringIO.StringIO(plaintext)
    cbuf = cStringIO.StringIO()
    ciphertext = _cipherFilter(cipher, pbuf, cbuf)
    pbuf.close()
    cbuf.close()
    assert ciphertext
    return ciphertext


class PasswordPrefs(Preferences):
    dummyPassword = schema.One(
        Password,
        doc = 'Dummy password. We need at least one password object always in the repository so that master password correctness can be checked.'
    )


def installParcel(parcel, oldVersion = None):
    dummyPassword = Password.update(parcel, 'dummyPassword')
    
    password = ''.join([string.printable[ord(c) % len(string.printable)] \
                        for c in os.urandom(16)])
    waitForDeferred(dummyPassword.encryptPassword(password, masterPassword=''))
    
    PasswordPrefs.update(parcel, 'passwordPrefs', dummyPassword=dummyPassword)
