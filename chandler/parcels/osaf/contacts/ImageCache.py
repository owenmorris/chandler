#!bin/env python

"""
 ImageCache class for loading and managing images, currently part of the
 Contacts parcel but soon to be moved into the core application
"""

__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2002, 2003 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from wxPython.wx import *
import urllib
import os
import string

class ImageCache:
    def __init__(self, basePath):
        self.basePath = basePath + os.sep + 'resources'
        self.images = {}

    def GetImageType(self, filename):
        segments = filename.split('.')
        extension = segments[-1]
        if extension == 'bmp':	
            imageType = wxBITMAP_TYPE_BMP
        elif extension == 'gif':
            imageType = wxBITMAP_TYPE_GIF
        elif extension == 'jpg':
            imageType = wxBITMAP_TYPE_JPEG
        elif extension == 'png':
            imageType = wxBITMAP_TYPE_PNG
        else:
            imageType = wxBITMAP_TYPE_ANY

        return imageType

    def GetImagePath(self, imageFilename):
        return self.basePath + os.sep + imageFilename
        
    def LoadBitmapURL(self, fileURL, maxWidth=None, maxHeight=None):
        urlParts = string.split(fileURL, '/')
        fileName = urlParts[-1]

        # for now, keep them in the same directory as the built-in ones
        # but we should change this soon
        filePath= self.basePath + os.sep + fileName

        # el cheapo image cache for now, that never purges; we'll
        # fix that soon
        if self.images.has_key(fileURL):
            return self.images[fileURL]

        try:		
            urllib.urlretrieve(fileURL, filePath)		
            imageType = self.GetImageType(fileName)
            image = wxImage(filePath, imageType)

            # handle scaling the image if necessary
            if maxWidth != None or maxHeight != None:
                imageWidth = image.GetWidth()
                imageHeight = image.GetHeight()

                if maxWidth != None and imageWidth > maxWidth:
                    scale = float(maxWidth) / float(imageWidth)
                    imageWidth = int(scale * imageWidth)
                    imageHeight = int(scale * imageHeight)

                if maxHeight != None and imageHeight > maxHeight:
                    scale = float(maxHeight) / float(imageHeight)
                    imageWidth = int(scale * imageWidth)
                    imageHeight = int(scale * imageHeight)	

                image.Rescale(imageWidth, imageHeight)

            bitmap = image.ConvertToBitmap()
            self.images[fileURL] = bitmap
        except:
            print "couldnt load image", fileURL, sys.exc_type, sys.exc_value
            bitmap = None

        return bitmap

    def LoadBitmapPath(self, bitmapPath):
        try:
            imageType = self.GetImageType(bitmapPath)
            image = wxImage(bitmapPath, imageType)
            bitmap = image.ConvertToBitmap()
        except:
            print "couldnt load image", bitmapPath, sys.exc_type, sys.exc_value
            bitmap = None

        return bitmap
        
    def LoadBitmapFile(self, filename):
        path = self.GetImagePath(filename)
        return self.LoadBitmapPath(path)
        
