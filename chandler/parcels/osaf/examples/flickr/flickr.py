"""
    flickr.py
    Copyright 2004 James Clarke <james@jamesclarke.info>

THIS SOFTWARE IS SUPPLIED WITHOUT WARRANTY OF ANY KIND, AND MAY BE
COPIED, MODIFIED OR DISTRIBUTED IN ANY WAY, AS LONG AS THIS NOTICE
AND ACKNOWLEDGEMENT OF AUTHORSHIP REMAIN.

This TODO list may not include recent API changes.
TODO (see TODO comments too):
* flickr.blogs, flickr.contacts, flickr.urls
* groups
    * flickr.groups.browse
    * flickr.groups.getActiveList
    * flickr.groups.pools.add
    * flickr.groups.pools.remove
* photosets
    * flickr.photosets.delete
    * flickr.photosets.editMeta
    * flickr.photosets.orderSets
* favorites
    * flickr.favorites.add
    * flickr.favorites.remove
* photos
    * flickr.photos.getContactsPhotos
    * flickr.photos.getPerms
    * flickr.photos.setPerms
    * flickr.photos.getCounts
    * flickr.photos.getUntagged
* notes for photos
"""

__author__ = "James Clarke <james@jamesclarke.info>"
__version__ = "$Rev: 18 $"
__date__ = "$Date: 2004-11-13 09:26:24 +0000 (Sat, 13 Nov 2004) $"
__copyright__ = "Copyright 2004 James Clarke"

from urllib import urlencode, urlopen
from xml.dom import minidom
from datetime import datetime

HOST = 'http://flickr.com'
API = '/services/rest'
# twl's API key
API_KEY = '63c3928cb39a3ab85740d9921cfd471e'
#Set email and password for auth
email = None
password = None

class FlickrError(Exception): pass

class Photo(object):
    """Represents a Flickr Photo."""

    #XXX: Hopefully None wont cause problems
    def __init__(self, id, owner=None, dateuploaded=None, \
                 title=None, description=None, ispublic=None, \
                 isfriend=None, isfamily=None, cancomment=None, \
                 canaddmeta=None, comments=None, tags=None):
        """Must specify id, rest is optional."""
        self.__loaded = False
        self.__id = id
        self.__owner = owner
        self.__dateuploaded = dateuploaded
        self.__datecreated = None
        self.__title = title
        self.__description = description
        self.__ispublic = ispublic
        self.__isfriend = isfriend
        self.__isfamily = isfamily
        self.__cancomment = cancomment
        self.__canaddmeta = canaddmeta
        self.__comments = comments
        self.__tags = tags

    
    #property mojo, ugly
    #make everything read only
    #TODO: maybe make title/description modifable and have the setters
    #      call setMeta.  Will result in two API calls instead of one
    #      if we change both title and description.  Cleaner though!
    id = property(lambda self: self._general_getattr('id'))
    owner = property(lambda self: self._general_getattr('owner'))
    dateuploaded = property(lambda self: \
                            self._general_getattr('dateuploaded'))
    datecreated = property(lambda self: \
                            self._general_getattr('datecreated'))
    title = property(lambda self: self._general_getattr('title'))
    description = property(lambda self: \
                           self._general_getattr('description'))
    ispublic = property(lambda self: self._general_getattr('ispublic'))
    isfriend = property(lambda self: self._general_getattr('isfriend'))
    isfamily = property(lambda self: self._general_getattr('family'))
    cancomment = property(lambda self: \
                          self._general_getattr('cancomment'))
    canaddmeta = property(lambda self: \
                          self._general_getattr('canaddmeta'))
    comments = property(lambda self: self._general_getattr('comments'))
    tags = property(lambda self: self._general_getattr('tags'))
    permcomment = property(lambda self: self._general_getattr('permcomment'))
    permaddmeta = property(lambda self: self._general_getattr('permaddmeta'))
    
    #XXX: I don't like this bit
    #     It would be nicer if I could pass the var (self.__id) into here
    #     But since _load_properties() modifies self.__id then the var
    #     is out of date when I return it.
    def _general_getattr(self, var):
        """Generic get attribute function."""
        if getattr(self, "_%s__%s" % (self.__class__.__name__, var)) is None \
           and not self.__loaded:
            self._load_properties()
        return getattr(self, "_%s__%s" % (self.__class__.__name__, var))

    #XXX: This is the one I like but it doesn't work
    #     here var is self.__id not 'id'
    #def _general_getattr(self, var):
    #    if var is None and not self.__loaded:
    #        self._load_properties()
    #    return var

    def _load_properties(self):
        """Loads the properties from Flickr."""
        method = 'flickr.photos.getInfo'
        data = _doget(method, photo_id=self.id)

        self.__loaded = True
        
        photo = data.rsp.photo
        self.__dateuploaded = datetime.fromtimestamp(int(photo.dates.posted))
        # Take a 2004-01-01 12:12:59 style string, turn - and : into whitespace
        munged_iso = photo.dates.taken.replace('-', ' ').replace(':', ' ')
        self.__datecreated = datetime(*map(int, munged_iso.split(' ')))

        owner = photo.owner
        self.__owner = User(owner.nsid, username=owner.username,\
                          realname=owner.realname,\
                          location=owner.location)

        self.__title = photo.title.text
        self.__description = photo.description.text
        self.__ispublic = photo.visibility.ispublic
        self.__isfriend = photo.visibility.isfriend
        self.__isfamily = photo.visibility.isfamily
        self.__cancomment = photo.editability.cancomment
        self.__canaddmeta = photo.editability.canaddmeta
        self.__comments = photo.comments.text
        
        #permissions may not exist
        try:
            self.__permcomment = photo.permissions.permcomment
        except:
            pass
        try:
            self.__permaddmeta = photo.permissions.permaddmeta
        except:
            pass

        #TODO: Implement Notes?

        try:#single tags aren't seen as iterable
            self.__tags = [tag.text for tag in photo.tags.tag]
        except TypeError:
            try:
                self.__tags = [photo.tags.tag.text]
            except:
                pass
        except AttributeError, ae:
            # handle the case where a photo has no tags
            pass 
        


    def __str__(self):
        return '<Flickr Photo %s>' % self.id    

    def setTags(self, tags):
        """Set the tags for current photo to list tags.
        (flickr.photos.settags)
        """
        method = 'flickr.photos.setTags'
        tags = uniq(tags)
        _doget(method, auth=True, photo_id=self.id, tags=tags)
        self.__tags = tags


    def addTags(self, tags):
        """Adds the list of tags to current tags. (flickr.photos.addtags)
        """
        method = 'flickr.photos.addTags'
        if isinstance(tags, list):
            tags = uniq(tags)

        _doget(method, auth=True, photo_id=self.id, tags=tags)

        #add new tags to old tags
        try:
            self.tags.extend(tags)
        except TypeError:
            self.tags.append(tags)
            
        self.__tags = uniq(self.tags)


    def setMeta(self, title=None, description=None):
        """Set metadata for photo. (flickr.photos.setMeta)"""
        method = 'flickr.photos.setMeta'

        if title is None:
            title = self.title
        if description is None:
            description = self.description
            
        _doget(method, auth=True, title=title, \
               description=description, photo_id=self.id)
        
        self.__title = title
        self.__description = description

    #TODO: I'm not too sure about this function, I would like a method
    #      to return all sizes but unsure on the data structure
    def getURL(self, size='Medium', urlType='url'):
        """Retrieves a url for the photo.  (flickr.photos.getSizes)

        urlType - 'url' or 'source'
        'url' - flickr page of photo
        'source' - image file
        """
        method = 'flickr.photos.getSizes'
        data = _doget(method, photo_id=self.id)
        for psize in data.rsp.sizes.size:
            if psize.label == size:
                return getattr(psize, urlType)
        raise FlickrError, "No URL found"
                
class Photoset(object):
    """A Flickr photoset."""

    def __init__(self, id, title, primary, photos=0, description=''):
        self.__id = id
        self.__title = title
        self.__primary = primary
        self.__description = description
        self.__n = photos
        
    id = property(lambda self: self.__id)
    title = property(lambda self: self.__title)
    description = property(lambda self: self.__description)
    primary = property(lambda self: self.__primary)

    def __len__(self):
        return self.__n

    def __str__(self):
        return '<Flickr Photoset %s>' % self.id
    
    def getPhotos(self):
        """Returns list of Photos."""
        method = 'flickr.photosets.getPhotos'
        data = _doget(method, photoset_id=self.id)
        photos = data.rsp.photoset.photo
        p = []
        for photo in photos:
            p.append(Photo(photo.id))
        return p    

    def editPhotos(self, photos, primary=None):
        """Edit the photos in this set.

        photos - photos for set
        primary - primary photo (if None will used current)
        """
        method = 'flickr.photosets.editPhotos'

        if primary is None:
            primary = self.primary
            
        ids = [photo.id for photo in photos]
        if primary.id not in ids:
            ids.append(primary.id)

        _doget(method, auth=True, photoset_id=self.id,\
               primary_photo_id=primary.id,
               photo_ids=ids)
        self.__n = len(ids)

    def create(cls, photo, title, description=''):
        """Create a new photoset.

        photo - primary photo
        """
        if not isinstance(photo, Photo):
            raise TypeError, "Photo expected"
        
        method = 'flickr.photosets.create'
        data = _doget(method, auth=True, title=title,\
                      description=description,\
                      primary_photo_id=photo.id)

        set = Photoset(data.rsp.photoset.id, title, Photo(photo.id),
                       photos=1, description=description)
        return set
    create = classmethod(create)


        
class User(object):
    """A Flickr user."""

    def __init__(self, id, username=None, isadmin=None, ispro=None, \
                 realname=None, location=None, firstdate=None, count=None):
        """id required, rest optional."""
        self.__loaded = False #so we don't keep loading data
        self.__id = id
        self.__username = username
        self.__isadmin = isadmin
        self.__ispro = ispro
        self.__realname = realname
        self.__location = location
        self.__photos_firstdate = firstdate
        self.__photos_count = count

    #property fu
    id = property(lambda self: self._general_getattr('id'))
    username = property(lambda self: self._general_getattr('username'))
    isadmin = property(lambda self: self._general_getattr('isadmin'))
    ispro = property(lambda self: self._general_getattr('ispro'))
    realname = property(lambda self: self._general_getattr('realname'))
    location = property(lambda self: self._general_getattr('location'))
    photos_firstdate = property(lambda self: \
                                self._general_getattr('photos_firstdate'))
    photos_count = property(lambda self: \
                            self._general_getattr('photos_count'))

    def _general_getattr(self, var):
        """Generic get attribute function."""
        if getattr(self, "_%s__%s" % (self.__class__.__name__, var)) is None \
           and not self.__loaded:
            self._load_properties()
        return getattr(self, "_%s__%s" % (self.__class__.__name__, var))
            
    def _load_properties(self):
        """Load User properties from Flickr."""
        method = 'flickr.people.getInfo'
        data = _doget(method, user_id=self.__id)

        self.__loaded = True
        
        person = data.rsp.person

        self.__isadmin = person.isadmin
        self.__ispro = person.ispro
        
        self.__username = person.username.text
        self.__realname = person.realname.text
        self.__location = person.location.text
        self.__photos_firstdate = person.photos.firstdate.text
        self.__photos_count = person.photos.count.text

    def __str__(self):
        return '<Flickr User %s>' % self.id
    
    def getPhotosets(self):
        """Returns a list of Photosets."""
        method = 'flickr.photosets.getList'
        data = _doget(method, user_id=self.id)
        sets = []
        for photoset in data.rsp.photosets.photoset:
            sets.append(Photoset(photoset.id, photoset.title,\
                                 Photo(photoset.primary),\
                                 description=photoset.description,
                                 photos=photoset.photos))
        return sets

class Group(object):
    """Flickr Group Pool"""
    def __init__(self, id, name=None, members=None, online=None,\
                 privacy=None, chatid=None, chatcount=None):
        self.__loaded = False
        self.__id = id
        self.__name = name
        self.__members = members
        self.__online = online
        self.__privacy = privacy
        self.__chatid = chatid
        self.__chatcount = chatcount

    id = property(lambda self: self._general_getattr('id'))
    name = property(lambda self: self._general_getattr('name'))
    members = property(lambda self: self._general_getattr('members'))
    online = property(lambda self: self._general_getattr('online'))
    privacy = property(lambda self: self._general_getattr('privacy'))
    chatid = property(lambda self: self._general_getattr('chatid'))
    chatcount = property(lambda self: self._general_getattr('chatcount'))
    
    def _general_getattr(self, var):
        """Generic get attribute function."""
        if getattr(self, "_%s__%s" % (self.__class__.__name__, var)) is None \
           and not self.__loaded:
            self._load_properties()
        return getattr(self, "_%s__%s" % (self.__class__.__name__, var))

    def _load_properties(self):
        """Loads the properties from Flickr."""
        method = 'flickr.groups.getInfo'
        data = _doget(method, group_id=self.id)

        self.__loaded = True
        
        group = data.rsp.group

        self.__name = photo.name.text
        self.__members = photo.members.text
        self.__online = photo.online.text
        self.__privacy = photo.privacy.text
        self.__chatid = photo.chatid.text
        self.__chatcount = photo.chatcount.text

    def __str__(self):
        return '<Flickr Group %s>' % self.id
    
    def getPhotos(self, tags='', per_page='', page=''):
        """Get a list of photo objects for this group"""
        method = 'flickr.groups.pools.getPhotos'
        data = _doget(method, group_id=self.id, tags=tags,\
                      per_page=per_page, page=page)
        photos = []
        for photo in data.rsp.photos.photo:
            photos.append(_parse_photo(photo))
        return photos
        
        
#Flickr API methods
#see api docs http://www.flickr.com/services/api/
#for details of each param

#XXX: Could just use photo.tags (as you'd already have Photo object)
def tags_getListPhoto(id):
    method = 'flickr.tags.getListPhoto'
    data = _doget(method, photo_id=id)
    return [tag.text for tag in data.rsp.photo.tags.tag]

#XXX: Should be in User as User.tags
def tags_getListUser(id=''):
    method = 'flickr.tags.getListUser'
    data = _doget(method, user_id=id)
    return [tag.text for tag in data.rsp.who.tags.tag]

#XXX: Could be in User
def tags_getListUserPopular(id='', count=''):
    #TODO: handle count? data.rsp.who.tags.tag.count
    method = 'flickr.tags.getListUserPopular'
    data = _doget(method, user_id=id, count=count)
    return [tag.text for tag in data.rsp.who.tags.tag]

#XXX: Could be Photo.search(cls)
def photos_search(user_id='', auth=False,  tags='', tag_mode='', text='',\
                  min_upload_date='', max_upload_date='',\
                  per_page='', page=''):
    """Returns a list of Photo objects.

    If auth=True then will auth the user.  Can see private etc
    """
    method = 'flickr.photos.search'

    data = _doget(method, auth=auth, user_id=user_id, tags=tags, text=text,\
                  min_upload_date=min_upload_date,\
                  max_upload_date=max_upload_date, per_page=per_page,\
                  page=page)
    photos = []
    for photo in data.rsp.photos.photo:
        photos.append(_parse_photo(photo))
    return photos

#XXX: Could be class method in User
def people_findByEmail(email):
    """Returns User object."""
    method = 'flickr.people.findByEmail'
    data = _doget(method, find_email=email)
    user = User(data.rsp.user.id, username=data.rsp.user.username.text)
    return user

def people_findByUsername(username):
    """Returns User object."""
    method = 'flickr.people.findByUsername'
    data = _doget(method, username=username)
    user = User(data.rsp.user.id, username=data.rsp.user.username.text)
    return user

#XXX: Should probably be in User as a list User.public
def people_getPublicPhotos(user_id, per_page='', page=''):
    """Returns list of Photo objects."""
    method = 'flickr.people.getPublicPhotos'
    data = _doget(method, user_id=user_id, per_page=per_page, page=page)
    photos = []
    for photo in data.rsp.photos.photo:
        photos.append(_parse_photo(photo))
    return photos

#XXX: Should probably be in User as User.favorites
def favorites_getList(user_id='', per_page='', page=''):
    """Returns list of Photo objects."""
    method = 'flickr.favorites.getList'
    data = _doget(method, auth=True, user_id=user_id, per_page=per_page,\
                  page=page)
    photos = []
    for photo in data.rsp.photos.photo:
        photos.append(_parse_photo(photo))
    return photos

def test_login():
    method = 'flickr.test.login'
    data = _doget(method, auth=True)
    user = User(data.rsp.user.id, username=data.rsp.user.username.text)
    return user

def test_echo():
    method = 'flickr.test.echo'
    data = _doget(method)
    return data.rsp.stat


#useful methods

def _doget(method, auth=False, **params):
    #uncomment to check you aren't killing the flickr server
    #print "***** do get %s" % method

    #convert lists to strings with ',' between items
    for (key, value) in params.items():
        if isinstance(value, list):
            params[key] = ','.join([item for item in value])
        
    url = '%s%s/?api_key=%s&method=%s&%s'% \
          (HOST, API, API_KEY, method, urlencode(params))
    if auth:
        url = url + '&email=%s&password=%s' % (email, password)

    #another useful debug print statement
    #print url
    
    xml = minidom.parse(urlopen(url))
    data = unmarshal(xml)
    if not data.rsp.stat == 'ok':
        msg = "ERROR [%s]: %s" % (data.rsp.err.code, data.rsp.err.msg)
        raise FlickrError, msg
    return data

def _parse_photo(photo):
    """Create a Photo object from photo data."""
    owner = User(photo.owner)
    title = photo.title
    ispublic = photo.ispublic
    isfriend = photo.isfriend
    isfamily = photo.isfamily
    p = Photo(photo.id, owner=owner, title=title, ispublic=ispublic,\
              isfriend=isfriend, isfamily=isfamily)        
    return p


#stolen methods

class Bag: pass

#unmarshal taken and modified from pyamazon.py
#makes the xml easy to work with
def unmarshal(element):
    rc = Bag()
    if isinstance(element, minidom.Element):
        for key in element.attributes.keys():
            setattr(rc, key, element.attributes[key].value)
            
    childElements = [e for e in element.childNodes \
                     if isinstance(e, minidom.Element)]
    if childElements:
        for child in childElements:
            key = child.tagName
            if hasattr(rc, key):
                if type(getattr(rc, key)) <> type([]):
                    setattr(rc, key, [getattr(rc, key)])
                setattr(rc, key, getattr(rc, key) + [unmarshal(child)])
            elif isinstance(child, minidom.Element) and \
                     (child.tagName == 'Details'):
                # make the first Details element a key
                setattr(rc,key,[unmarshal(child)])
                #dbg: because otherwise 'hasattr' only tests
                #dbg: on the second occurence: if there's a
                #dbg: single return to a query, it's not a
                #dbg: list. This module should always
                #dbg: return a list of Details objects.
            else:
                setattr(rc, key, unmarshal(child))
    else:
        #jec: we'll have the main part of the element stored in .text
        #jec: will break if tag <text> is also present
        text = "".join([e.data for e in element.childNodes \
                        if isinstance(e, minidom.Text)])
        setattr(rc, 'text', text)
    return rc

#unique items from a list from the cookbook
def uniq(alist):    # Fastest without order preserving
    set = {}
    map(set.__setitem__, alist, [])
    return set.keys()

if __name__ == '__main__':
    print test_echo()
    # test
    # fails because a single photo doesn't work with photos_search
    #photo = photos_search(tags='apachecon', per_page=1)[0]
    photo = photos_search(tags='apachecon', per_page=2)[1]
    photos = people_getPublicPhotos(people_findByUsername('sprout').id, 10)
    #for p in photos:
    #    print p.tags
