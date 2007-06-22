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

from application import schema
from application.dialogs.AccountPreferences import AccountPanel
from i18n import MessageFactory
_ = MessageFactory("Chandler-gdataPlugin")


import logging
logger = logging.getLogger(__name__)

from classes import *
from ui import *


def installParcel(parcel, oldVersion=None):

    parentMenu = schema.ns('osaf.views.main', parcel).ExperimentalMenu
    makeGdataMenu(parcel, parentMenu)

    AccountPanel.update(parcel, "GDataAccountPanel",
        accountClass = GDataAccount,
        key = "SHARING_GDATA",
        info = {
            "fields" : {
                "GDATASHARING_DESCRIPTION" : {
                    "attr" : "displayName",
                    "type" : "string",
                    "required" : True,
                    "default": _(u"New Google Sharing Account"),
                },
                "GDATASHARING_USERNAME" : {
                    "attr" : "username",
                    "type" : "string",
                },
                "GDATASHARING_PASSWORD" : {
                    "attr" : "password",
                    "type" : "password",
                },
            },
            "id" : "GDATASHARINGPanel",
            "order": 100, # after OOTB accounts
            "displayName" : "GDATASHARING_DESCRIPTION",
            "description" : _(u"Google sharing"),
            "protocol" : "GDATA",
        },
        xrc = """<?xml version="1.0" encoding="ISO-8859-15"?>
<resource>
  <object class="wxPanel" name="GDATASHARINGPanel">
    <object class="wxBoxSizer">
      <orient>wxVERTICAL</orient>
      <object class="sizeritem">
        <flag>wxALIGN_CENTER|wxALL</flag>
        <border>5</border>
        <object class="wxFlexGridSizer">
          <cols>2</cols>
          <rows>0</rows>
          <vgap>0</vgap>
          <hgap>0</hgap>
          <object class="sizeritem">
            <flag>wxALIGN_CENTER|wxALL</flag>
            <border>5</border>
            <object class="wxStaticText" name="ID_TEXT">
              <size>110,-1</size>
              <style>wxALIGN_RIGHT</style>
              <label>Account type:</label>
            </object>
          </object>
          <object class="sizeritem">
            <flag>wxALIGN_CENTER_VERTICAL|wxALL</flag>
            <border>5</border>
            <object class="wxStaticText" name="ID_TEXT">
              <size>300,-1</size>
              <label>Google Calendar sharing</label>
            </object>
          </object>
          <object class="sizeritem">
            <flag>wxALIGN_CENTER|wxALL</flag>
            <border>5</border>
            <object class="wxStaticText" name="ID_TEXT">
              <size>110,-1</size>
              <style>wxALIGN_RIGHT</style>
              <label>Descr&amp;iption:</label>
            </object>
          </object>
          <object class="sizeritem">
            <flag>wxALIGN_CENTER_VERTICAL|wxALL</flag>
            <border>5</border>
            <object class="wxTextCtrl" name="GDATASHARING_DESCRIPTION">
              <size>300,-1</size>
              <value></value>
            </object>
          </object>
          <object class="sizeritem">
            <flag>wxALIGN_CENTER|wxALL</flag>
            <border>5</border>
            <object class="wxStaticText" name="ID_TEXT">
              <size>110,-1</size>
              <style>wxALIGN_RIGHT</style>
              <label>User &amp;name:</label>
            </object>
          </object>
          <object class="sizeritem">
            <flag>wxALIGN_CENTER_VERTICAL|wxALL</flag>
            <border>5</border>
            <object class="wxTextCtrl" name="GDATASHARING_USERNAME">
              <size>300,-1</size>
              <value></value>
            </object>
          </object>
          <object class="sizeritem">
            <flag>wxALIGN_CENTER|wxALL</flag>
            <border>5</border>
            <object class="wxStaticText" name="ID_TEXT">
              <size>110,-1</size>
              <style>wxALIGN_RIGHT</style>
              <label>Pass&amp;word:</label>
            </object>
          </object>
          <object class="sizeritem">
            <flag>wxALIGN_CENTER_VERTICAL|wxALL</flag>
            <border>5</border>
            <object class="wxTextCtrl" name="GDATASHARING_PASSWORD">
              <size>300,-1</size>
              <style>wxTE_PASSWORD</style>
              <value></value>
            </object>
          </object>
        </object>
      </object>
    </object>
  </object>
</resource>
"""
    )
