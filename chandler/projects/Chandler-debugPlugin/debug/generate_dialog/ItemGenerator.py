# -*- coding: utf-8 -*-
#   Copyright (c) 2008 Open Source Applications Foundation
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


import wx
from wx import xrc
import application.Globals as Globals
import os 
import pkg_resources
import logging
from debug import createItems as createItems 
import cPickle as pickle
import itemGenHelp_xrc as itemGenHelp_xrc
from datetime import date 

if bool(wx.GetApp()): 
    import tools.QAUITestAppLib as QAUITestAppLib #import only if we really have a Chandler window
else:
    from chandlerdb.persistence.RepositoryView import NullRepositoryView #import for tests

logger = logging.getLogger(__name__)
__res = None


def get_resources():
    """ This function provides access to the XML resources in this module."""
    global __res
    if __res == None:
        __init_resources()
    return __res


class xrcFRAME1(wx.Dialog):
    def PreCreate(self, pre):
        """ This function is called during the class's initialization.

        Override it for custom setup before the window is created usually to
        set additional window styles using SetWindowStyle() and SetExtraStyle()."""
        pass

    def __init__(self, parent):
        # Two stage creation (see http://wiki.wxpython.org/index.cgi/TwoStageCreation)
        pre = wx.PreDialog()
        self.PreCreate(pre)
        get_resources().LoadOnDialog(pre, parent, "FRAME1")
        self.PostCreate(pre)
        #more manually added stuff
        self.InitButtons()

    # create attributes for the named items in this container
        self.noteBookContainer = xrc.XRCCTRL(self, "noteBookContainer")
        self.pageGeneral = xrc.XRCCTRL(self, "pageGeneral")
        self.labelGeneralPage = xrc.XRCCTRL(self, "labelGeneralPage")
        self.labelTotalItems = xrc.XRCCTRL(self, "labelTotalItems")
        self.textCtrlTotalItems = xrc.XRCCTRL(self, "textCtrlTotalItems")
        self.labelNumOfItemsValid = xrc.XRCCTRL(self, "labelNumOfItemsValid")
        self.labelStamps = xrc.XRCCTRL(self, "labelStamps")
        self.labelPercentTask = xrc.XRCCTRL(self, "labelPercentTask")
        self.choicePercentTask = xrc.XRCCTRL(self, "choicePercentTask")
        self.labelPercentMail = xrc.XRCCTRL(self, "labelPercentMail")
        self.choicePercentMail = xrc.XRCCTRL(self, "choicePercentMail")
        self.labelPercentEvent = xrc.XRCCTRL(self, "labelPercentEvent")
        self.choicePercentEvent = xrc.XRCCTRL(self, "choicePercentEvent")
        self.labelStampsValid = xrc.XRCCTRL(self, "labelStampsValid")
        self.labelTitle = xrc.XRCCTRL(self, "labelTitle")
        self.textCtrlTitleSourceFile = xrc.XRCCTRL(self, "textCtrlTitleSourceFile")
        self.labelTitleSourceValid = xrc.XRCCTRL(self, "labelTitleSourceValid")
        self.labelNoteField = xrc.XRCCTRL(self, "labelNoteField")
        self.textCtrlNoteSourceFilePath = xrc.XRCCTRL(self, "textCtrlNoteSourceFilePath")
        self.labelNoteSourceValid = xrc.XRCCTRL(self, "labelNoteSourceValid")
        self.labelCollectionSource = xrc.XRCCTRL(self, "labelCollectionSource")
        self.textCtrlCollectionFileName = xrc.XRCCTRL(self, "textCtrlCollectionFileName")
        self.labelCollectionSourceValid = xrc.XRCCTRL(self, "labelCollectionSourceValid")
        self.labelNumberOfCollections = xrc.XRCCTRL(self, "labelNumberOfCollections")
        self.textCtrlCollectionCount = xrc.XRCCTRL(self, "textCtrlCollectionCount")
        self.labelCollectionCountValid = xrc.XRCCTRL(self, "labelCollectionCountValid")
        self.labelCollectionMembership = xrc.XRCCTRL(self, "labelCollectionMembership")
        self.textCtrlCollectionMembership = xrc.XRCCTRL(self, "textCtrlCollectionMembership")
        self.labelCollectionMembershipValid = xrc.XRCCTRL(self, "labelCollectionMembershipValid")
        self.labelNoteField = xrc.XRCCTRL(self, "labelNoteField")
        self.textCtrlLocationSourceFilePath = xrc.XRCCTRL(self, "textCtrlLocationSourceFilePath")
        self.labelLocationSourceValid = xrc.XRCCTRL(self, "labelLocationSourceValid")
        self.labelTriageStatus = xrc.XRCCTRL(self, "labelTriageStatus")
        self.labelPercentUnassignedStatus = xrc.XRCCTRL(self, "labelPercentUnassignedStatus")
        self.choicePercentUnassignedStatus = xrc.XRCCTRL(self, "choicePercentUnassignedStatus")
        self.labelPercentNow = xrc.XRCCTRL(self, "labelPercentNow")
        self.choicePercentNow = xrc.XRCCTRL(self, "choicePercentNow")
        self.labelPercentLater = xrc.XRCCTRL(self, "labelPercentLater")
        self.choicePercentLater = xrc.XRCCTRL(self, "choicePercentLater")
        self.labelPercentDone = xrc.XRCCTRL(self, "labelPercentDone")
        self.choicePercentDone = xrc.XRCCTRL(self, "choicePercentDone")
        self.labelTriageValid = xrc.XRCCTRL(self, "labelTriageValid")
        self.pageEvent = xrc.XRCCTRL(self, "pageEvent")
        self.labelEventPage = xrc.XRCCTRL(self, "labelEventPage")
        self.labelTimePeriod = xrc.XRCCTRL(self, "labelTimePeriod")
        self.labelStartDate = xrc.XRCCTRL(self, "labelStartDate")
        self.textCtrlStartDate = xrc.XRCCTRL(self, "textCtrlStartDate")
        self.labelEndDate = xrc.XRCCTRL(self, "labelEndDate")
        self.textCtrlEndDate = xrc.XRCCTRL(self, "textCtrlEndDate")
        self.labelDateRangeValid = xrc.XRCCTRL(self, "labelDateRangeValid")
        self.labelTimeOfDay = xrc.XRCCTRL(self, "labelTimeOfDay")
        self.textCtrlTimeOfDay = xrc.XRCCTRL(self, "textCtrlTimeOfDay")
        self.labelTimeOfDaySpecValid = xrc.XRCCTRL(self, "labelTimeOfDaySpecValid")
        self.labelDuration = xrc.XRCCTRL(self, "labelDuration")
        self.textCtrlDuration = xrc.XRCCTRL(self, "textCtrlDuration")
        self.labelDurationSpecValid = xrc.XRCCTRL(self, "labelDurationSpecValid")
        self.labelDurationTypes = xrc.XRCCTRL(self, "labelDurationTypes")
        self.labelPercentAllDay = xrc.XRCCTRL(self, "labelPercentAllDay")
        self.choicePercentAllDay = xrc.XRCCTRL(self, "choicePercentAllDay")
        self.labelPercentAtTime = xrc.XRCCTRL(self, "labelPercentAtTime")
        self.choicePercentAtTime = xrc.XRCCTRL(self, "choicePercentAtTime")
        self.labelPercentAnyTime = xrc.XRCCTRL(self, "labelPercentAnyTime")
        self.choicePercentAnyTime = xrc.XRCCTRL(self, "choicePercentAnyTime")
        self.labelPercentDuration = xrc.XRCCTRL(self, "labelPercentDuration")
        self.choicePercentDuration = xrc.XRCCTRL(self, "choicePercentDuration")
        self.labelDurationTypesValid = xrc.XRCCTRL(self, "labelDurationTypesValid")
        self.labelStatus = xrc.XRCCTRL(self, "labelStatus")
        self.labelPercentConfirmed = xrc.XRCCTRL(self, "labelPercentConfirmed")
        self.choicePercentConfirmed = xrc.XRCCTRL(self, "choicePercentConfirmed")
        self.labelPercentTentative = xrc.XRCCTRL(self, "labelPercentTentative")
        self.choicePercentTentative = xrc.XRCCTRL(self, "choicePercentTentative")
        self.labelPercentFYI = xrc.XRCCTRL(self, "labelPercentFYI")
        self.choicePercentFYI = xrc.XRCCTRL(self, "choicePercentFYI")
        self.labelStatusValid = xrc.XRCCTRL(self, "labelStatusValid")
        self.labelRecurrence = xrc.XRCCTRL(self, "labelRecurrence")
        self.labelPercentNonRecurring = xrc.XRCCTRL(self, "labelPercentNonRecurring")
        self.choicePercentNonRecurring = xrc.XRCCTRL(self, "choicePercentNonRecurring")
        self.labelPercentDaily = xrc.XRCCTRL(self, "labelPercentDaily")
        self.choicePercentDaily = xrc.XRCCTRL(self, "choicePercentDaily")
        self.labelPercentWeekly = xrc.XRCCTRL(self, "labelPercentWeekly")
        self.choicePercentWeekly = xrc.XRCCTRL(self, "choicePercentWeekly")
        self.labelPercentBiWeekly = xrc.XRCCTRL(self, "labelPercentBiWeekly")
        self.choicePercentBiWeekly = xrc.XRCCTRL(self, "choicePercentBiWeekly")
        self.labelPercentMonthly = xrc.XRCCTRL(self, "labelPercentMonthly")
        self.choicePercentMonthly = xrc.XRCCTRL(self, "choicePercentMonthly")
        self.labelPercentYearly = xrc.XRCCTRL(self, "labelPercentYearly")
        self.choicePercentYearly = xrc.XRCCTRL(self, "choicePercentYearly")
        self.labelRecurrenceValid = xrc.XRCCTRL(self, "labelRecurrenceValid")
        self.labelRecurrenceEndDate = xrc.XRCCTRL(self, "labelRecurrenceEndDate")
        self.textCtrlRecurrenceEndDates = xrc.XRCCTRL(self, "textCtrlRecurrenceEndDates")
        self.labelRecurrenceEndDateValid = xrc.XRCCTRL(self, "labelRecurrenceEndDateValid")
        self.labelAlarmSpecification = xrc.XRCCTRL(self, "labelAlarmSpecification")
        self.textCtrlAlarmSpec = xrc.XRCCTRL(self, "textCtrlAlarmSpec")
        self.labelAlarmTypeValid = xrc.XRCCTRL(self, "labelAlarmTypeValid")
        self.pageMessage = xrc.XRCCTRL(self, "pageMessage")
        self.labelMsgPage = xrc.XRCCTRL(self, "labelMsgPage")
        self.labelTo = xrc.XRCCTRL(self, "labelTo")
        self.labelToFile = xrc.XRCCTRL(self, "labelToFile")
        self.textCtrlToFile = xrc.XRCCTRL(self, "textCtrlToFile")
        self.labelToSourceValid = xrc.XRCCTRL(self, "labelToSourceValid")
        self.labelToSpec = xrc.XRCCTRL(self, "labelToSpec")
        self.textCtrlToSpec = xrc.XRCCTRL(self, "textCtrlToSpec")
        self.labelToSpecValid = xrc.XRCCTRL(self, "labelToSpecValid")
        self.labelCC = xrc.XRCCTRL(self, "labelCC")
        self.labelCCFileName = xrc.XRCCTRL(self, "labelCCFileName")
        self.textCtrlCCFileName = xrc.XRCCTRL(self, "textCtrlCCFileName")
        self.labelCCSourceValid = xrc.XRCCTRL(self, "labelCCSourceValid")
        self.labelCCSpec = xrc.XRCCTRL(self, "labelCCSpec")
        self.textCtrlCCSpec = xrc.XRCCTRL(self, "textCtrlCCSpec")
        self.labelCCSpecValid = xrc.XRCCTRL(self, "labelCCSpecValid")
        self.labelBCC = xrc.XRCCTRL(self, "labelBCC")
        self.labelCtrlBCCFileName = xrc.XRCCTRL(self, "labelCtrlBCCFileName")
        self.textCtrlBCCFileName = xrc.XRCCTRL(self, "textCtrlBCCFileName")
        self.labelBCCSourceValid = xrc.XRCCTRL(self, "labelBCCSourceValid")
        self.labelNumBCCSpec = xrc.XRCCTRL(self, "labelNumBCCSpec")
        self.textCtrlBCCSpec = xrc.XRCCTRL(self, "textCtrlBCCSpec")
        self.labelBCCSpecValid = xrc.XRCCTRL(self, "labelBCCSpecValid")
        self.addressFieldNote = xrc.XRCCTRL(self, "addressFieldNote")
        self.buttonGenerate = xrc.XRCCTRL(self, "buttonGenerate")
        self.buttonCancel = xrc.XRCCTRL(self, "buttonCancel")
        self.buttonSave = xrc.XRCCTRL(self, "buttonSave")
        self.buttonRestore = xrc.XRCCTRL(self, "buttonRestore")
        self.buttonHelp = xrc.XRCCTRL(self, "buttonHelp")

# ------------------------ end auto generated code ----------------------

    def OnCancel(self, evt):
        self.Show(show=False)
        self.Close()

    def OnSave(self, evt):
        fname = 'itemGeneratorSettings.pickle'
        try:
            f = open(fname, 'w')
            pickle.dump(self.valuesToDict(), f)
        except:
            print "\n\nUnable to open %s\n\n" % fname
        finally:
            f.close()

    def OnRestore(self, evt):
        fname = 'itemGeneratorSettings.pickle'
        try:
            f = open(fname, 'r')
            valueDict = pickle.load(f)
        except:
            print "\n\nUnable to open %s\n\n" % fname
        finally:
            f.close()
        self.restoreDialogValues(valueDict)

    def OnHelp(self, evt):    
        self.helpWin = itemGenHelp_xrc.xrcHelpWin(self)
        self.helpWin.Show()

    def valuesToDict(self):
        """ returns a dict containing all dialog values as ctrlName:ctrlValue """
        dialogValues = {}
        for ctrl in [ctrl for ctrl in dir(self)]:
            if 'textCtrl' in ctrl:
                dialogValues[ctrl] = self.__dict__[ctrl].GetValue()
            elif 'choice' in ctrl:
                dialogValues[ctrl] = self.__dict__[ctrl].GetStringSelection()
        return dialogValues

    def restoreDialogValues(self, valueDict):
        """given a dict of ctrlName:ctrlValue pairs repopulates dialog with values"""
        for ctrl in valueDict.iterkeys():
            if 'textCtrl' in ctrl:
                self.__dict__[ctrl].SetValue(valueDict[ctrl])
            if 'choice' in ctrl:
                self.__dict__[ctrl].SetStringSelection(valueDict[ctrl])

    def OnGenerate(self, evt): 
        if self.validate():
            self.Close()
            createItems.createItems(self.valuesToDict())
        else:
            msg ="Some input is invalid.  Please correct input with 'Error' to the right of it and try again"
            wx.MessageDialog(self, msg, caption='Input error', style=wx.OK, pos=wx.DefaultPosition).ShowModal()

    def InitButtons(self):
        wx.EVT_BUTTON(self, xrc.XRCID("buttonCancel"), self.OnCancel)
        wx.EVT_BUTTON(self, xrc.XRCID("buttonGenerate"), self.OnGenerate)
        wx.EVT_BUTTON(self, xrc.XRCID("buttonSave"), self.OnSave)
        wx.EVT_BUTTON(self, xrc.XRCID("buttonRestore"), self.OnRestore)
        wx.EVT_BUTTON(self, xrc.XRCID("buttonHelp"), self.OnHelp)

    ## validate dialog inputs    

    def isNumericAndNonZero(self, ctrl):
        """Test that a control contains a non zero numeric value"""
        val = ctrl.GetValue()
        return val.isdigit() and int(val) > 0

    def isValidPath(self, path):
        """Test that data file exists"""
        if os.path.lexists(path):
            return True
        elif os.path.lexists(os.path.join(Globals.chandlerDirectory, 'projects/Chandler-debugPlugin/debug', path)):
            return True
        return False 
    
    def collectionCountNotExceeded(self, spec, totalCollectionCount):
        """Test that no membership spec requires more collections than the total
        number of collections created (totalCollectionCount).
        """
        collectionCounts = [int(x.strip()[0]) for x in spec.split(',')]
        collectionCounts.sort()
        return collectionCounts.pop() <= totalCollectionCount

    def sumValueIs100(self, *controls):
        """Returns true if the sum of all _choice_ control values is == 100"""
        sum = 0
        for ctrl in controls:
            sum += int(ctrl.GetStringSelection())
        return sum == 100

    def datesCorrect(self, start, end):
        """Test that start and end are valid dates and start is before end"""
        try:
            y,m,d = start.split(',')
            startDate = date(int(y),int(m),int(d))
            y,m,d = end.split(',')
            endDate = date(int(y),int(m),int(d))
            diff = endDate - startDate
            return diff.days > 0
        except:
            return False 


    def tryToProcess(self, func, *args):
        """Try to process dialog textValue with its associated function.
        Return True if no errors"""
        try:
            func(*args) 
        except:
            return False
        return True 

    def validate(self):
        """Attempts to check that all settings in dialog are valid."""
        
        if bool(wx.GetApp()):
            view = QAUITestAppLib.App_ns.itsView
        else: # when running unit tests there is no app
            view = NullRepositoryView(verify=True)

        tzinfo = view.tzinfo.getDefault()

        self.output = True

        def _markValid(isValid, label):
            """mark control as 'Valid' or 'Error'"""
            if isValid:
                label.ForegroundColour='black'
                label.SetLabel('Valid')
            else:
                label.ForegroundColour='red'
                label.SetLabel('Error')
                self.output = False

        # test total items
        result = self.isNumericAndNonZero(self.textCtrlTotalItems)
        _markValid(result, self.labelNumOfItemsValid)

        # mark stamp percentages valid (all possible input is valid)
        _markValid(True, self.labelStampsValid)

        # test title source
        result = self.isValidPath(self.textCtrlTitleSourceFile.GetValue())
        _markValid(result, self.labelTitleSourceValid)

        # test note source
        result = self.isValidPath(self.textCtrlNoteSourceFilePath.GetValue())      
        _markValid(result, self.labelNoteSourceValid)

        # test collection source
        result = self.isValidPath(self.textCtrlCollectionFileName.GetValue())
        _markValid(result, self.labelCollectionSourceValid)

        # test number of collections
        result = self.isNumericAndNonZero(self.textCtrlCollectionCount)
        _markValid(result, self.labelCollectionCountValid)
        
        # test collection membership
        membershipSpec = self.textCtrlCollectionMembership.GetValue()
        totalCollectionCount = int(self.textCtrlCollectionCount.GetValue())
        result = self.tryToProcess(createItems.createMembershipIndex, membershipSpec, totalCollectionCount) \
            and \
            self.collectionCountNotExceeded(membershipSpec, totalCollectionCount)
        _markValid(result, self.labelCollectionMembershipValid)

        # test location source
        result = self.isValidPath(self.textCtrlLocationSourceFilePath.GetValue())
        _markValid(result, self.labelLocationSourceValid)

        # test triage percentaqes
        result = self.sumValueIs100(self.choicePercentUnassignedStatus, 
                                    self.choicePercentNow,
                                    self.choicePercentLater, 
                                    self.choicePercentDone )
        _markValid(result, self.labelTriageValid)

        # test start/ end dates
        result = self.datesCorrect(self.textCtrlStartDate.GetValue(), self.textCtrlEndDate.GetValue())
        _markValid(result, self.labelDateRangeValid)

        # test time of day spec
        result = self.tryToProcess(createItems.createStartTimeRange,self.textCtrlTimeOfDay.GetValue(), [1,2,3])
        _markValid(result, self.labelTimeOfDaySpecValid)

        # test duration spec
        result = self.tryToProcess(createItems.createDurationIndex, self.textCtrlDuration.GetValue(), [1,2,3])
        _markValid(result, self.labelDurationSpecValid) 

        # test duration type percentages
        result = self.sumValueIs100(self.choicePercentAllDay,
                                    self.choicePercentAtTime,
                                    self.choicePercentAnyTime,
                                    self.choicePercentDuration)
        _markValid(result, self.labelDurationTypesValid)

        # test status percentages
        result = self.sumValueIs100(self.choicePercentConfirmed,
                                    self.choicePercentTentative,
                                    self.choicePercentFYI)
        _markValid(result, self.labelStatusValid)

        # test recurrence percentages
        result = self.sumValueIs100(self.choicePercentNonRecurring,
                                    self.choicePercentDaily,
                                    self.choicePercentWeekly,
                                    self.choicePercentBiWeekly,
                                    self.choicePercentMonthly,
                                    self.choicePercentYearly)
        _markValid(result, self.labelRecurrenceValid)

        # test recurrence end date spec
        result = self.tryToProcess(createItems.createEndDateIndex, self.textCtrlRecurrenceEndDates.GetValue(), [1,2,3])
        _markValid(result, self.labelRecurrenceEndDateValid)

        # test alarm spec
        result = self.tryToProcess(createItems.createAlarmIndex, self.textCtrlAlarmSpec.GetValue(), [1,2,3], [1,2,3,4], tzinfo)
        _markValid(result, self.labelAlarmTypeValid)

        # test To source file
        result = self.isValidPath(self.textCtrlToFile.GetValue())
        _markValid(result, self.labelToSourceValid)

        # test To spec
        result = self.tryToProcess(createItems.createAddressIndex, [1,2,3], self.textCtrlToSpec.GetValue(), [1,2,3])
        _markValid(result, self.labelToSpecValid)

        # test CC source file
        result = self.isValidPath(self.textCtrlCCFileName.GetValue())
        _markValid(result, self.labelCCSourceValid)

        # test CC spec
        result = self.tryToProcess(createItems.createAddressIndex, [1,2,3], self.textCtrlCCSpec.GetValue(), [1,2,3])
        _markValid(result, self.labelCCSpecValid)

        # test BCC source file
        result = self.isValidPath(self.textCtrlBCCFileName.GetValue())
        _markValid(result, self.labelBCCSourceValid)

        # test To spec
        result = self.tryToProcess(createItems.createAddressIndex, [1,2,3], self.textCtrlBCCSpec.GetValue(), [1,2,3])
        _markValid(result, self.labelBCCSpecValid)

        return self.output 

def __init_resources():
    global __res
    xml = pkg_resources.resource_string(__name__, 'ItemGenerator.xrc')
    __res = xrc.EmptyXmlResource()
    __res.LoadFromString(xml)

def show():
    dialogWin = xrcFRAME1(None)
    dialogWin.Show()

def showStandAlone():
    app = wx.PySimpleApp()
    dialog = xrcFRAME1(None)
    result = dialog.Show()



if __name__ == '__main__':
    showStandAlone()
