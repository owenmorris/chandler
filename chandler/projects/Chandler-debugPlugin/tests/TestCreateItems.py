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


import unittest
from debug import createItems 
import datetime
from chandlerdb.persistence.RepositoryView import NullRepositoryView
from osaf import pim
import osaf.pim.calendar.Calendar as Calendar

class TestCreateItems(unittest.TestCase):
    
    def setUp(self):
        self.view = NullRepositoryView(verify=True)
        self.tzinfo = self.view.tzinfo.getInstance("US/Pacific")
        
    def tearDown(self):
        pass 
    
    def testpercentsToCount1(self):
        self.fruit = {'apples':20, 'oranges':15, 'banana':25}
        #test with total as an integer, percentages add to less than 100
        result = createItems.percentsToCount(20, self.fruit)
        self.assertEqual(result, {'apples': [0, 1, 2, 3], 
                                  'oranges': [4, 5, 6], 
                                  'banana': [7, 8, 9, 10, 11]})
        
    def testpercentsToCount2(self):    
        #test with total as a range, percentages add to less than 100
        self.fruit = {'apples':20, 'oranges':15, 'banana':25}
        result = createItems.percentsToCount([0,1,2,3,4,5,6,7,8,9], self.fruit)
        self.assertEqual(result, {'apples': [0, 1], 
                                  'oranges': [2], 
                                  'banana': [3, 4]})
        
    def testpercentsToCount3(self):    
        #test with total as an integer, percentages add to 100
        self.fruit={'apples':50, 'oranges':25, 'banana':25}
        result = createItems.percentsToCount(20, self.fruit)
        self.assertEqual(result, {'apples': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9], 
                                  'oranges': [10, 11, 12, 13, 14], 
                                  'banana': [15, 16, 17, 18, 19]})
        
    def testpercentsToCount4(self):   
        #test with total as an integer, percentages sum to more than 100
        fruit={'apples':50, 'oranges':50, 'banana':50}
        result = createItems.percentsToCount(30, fruit)
        self.assertEqual(result, 
            {'apples': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14], 
           'oranges': [15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 
                       29], 
           'banana': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14]})
        
    def testMkRanges1(self):
        """
        """
        fruit = {'apples':20, 'oranges':15, 'banana':25}
        # indexes == number of items
        result = createItems.mkRanges(1, 60, fruit)
        self.assertEqual(result, 
                {'apples': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 
                            16, 17, 18, 19, 20], 
                'oranges': [21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 
                            34, 35], 
                'banana': [36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 
                           49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60]})
        
    def testMkRanges2(self):
        # indexes less than number of items
        fruit = {'apples':20, 'oranges':15, 'banana':25}
        result = createItems.mkRanges(1,20,fruit)
        self.assertEqual(result, {'apples': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 
                            12, 13, 14, 15, 16, 17, 18, 19, 20], 
                        'oranges': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 
                            14, 15], 
                        'banana': [16, 17, 18, 19, 20, 1, 2, 3, 4, 5, 6, 7, 8, 
                            9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 
                            20]})
           
    def testMkRanges3(self):
        # indexes greater than number of items
        fruit = {'apples':20, 'oranges':15, 'banana':25}
        result = createItems.mkRanges(1,100,fruit)
        self.assertEqual(result, {
            'apples': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 
                        12, 13, 14, 15, 16, 17, 18, 19, 20], 
            'oranges': [21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 
                        35], 
            'banana': [36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 
                       50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60]})
        
    def testRandomize1(self):
        #test that values change order after randomizing
        test = {'a':[1,2,3], 'b':[4,5,6], 'c':[7,8,9]}
        rand = createItems.randomizeDict(test)
        self.assertNotEqual(test['a'], rand['a'])
        
    def testRandomize2(self):
        #test that randomized dict still has all the same vailues
        test = {'a':[1,2,3], 'b':[4,5,6], 'c':[7,8,9]}
        rand = createItems.randomizeDict(test)
        sortedList = []
        for subList in rand.itervalues():
            sortedList += subList
        sortedList.sort()
        self.assertEqual(sortedList, [1,2,3,4,5,6,7,8,9])
      
    def testCreateDurationIndex1(self):
        # 100% of the items have a duration of 1 hour and 1 minute
        self.assertEqual(createItems.createDurationIndex('1.1:100',
                                                [0,1,2,3,4,5,6,7,8,9]), 
                                                {
                                               0: datetime.timedelta(0, 3660), 
                                               1: datetime.timedelta(0, 3660), 
                                               2: datetime.timedelta(0, 3660), 
                                               3: datetime.timedelta(0, 3660), 
                                               4: datetime.timedelta(0, 3660), 
                                               5: datetime.timedelta(0, 3660), 
                                               6: datetime.timedelta(0, 3660), 
                                               7: datetime.timedelta(0, 3660), 
                                               8: datetime.timedelta(0, 3660), 
                                               9: datetime.timedelta(0, 3660)})
    
    def testCreateDurationIndex2(self):
        # a more complicated duration spec
        values = createItems.createDurationIndex('3.0:30, 0.3:30, 9.59:40',
                                                 [0,1,2,3,4,5,6,7,8,9]).values()
        values.sort() # unrandomize result
        self.assertEqual(values, [datetime.timedelta(0, 180), 
                                  datetime.timedelta(0, 180), 
                                  datetime.timedelta(0, 180), 
                                  datetime.timedelta(0, 10800), 
                                  datetime.timedelta(0, 10800), 
                                  datetime.timedelta(0, 10800), 
                                  datetime.timedelta(0, 35940), 
                                  datetime.timedelta(0, 35940), 
                                  datetime.timedelta(0, 35940), 
                                  datetime.timedelta(0, 35940)])
        
    def testCreateEndDateIndex1(self):
        # test 100% the same end spec
        self.assertEqual(createItems.createEndDateIndex('10:100',[1,2,3,4,5]), 
                                         {1: 10, 2: 10, 3: 10, 4: 10, 5: 10})

    def testCreateEndDateIndex2(self):
        # test mixed spec
        values = createItems.createEndDateIndex('3:30,6:30,10:40', 
                                                [1,2,3,4,5,6,7,8,9,10]).values()
        values.sort() # unrandomize
        self.assertEqual(values, [3, 3, 3, 6, 6, 6, 10, 10, 10, 10])
    
    #def testCalcEndDate(self):
        ##
        #frequencies = ['daily','weekly','biweekly','monthly', 'yearly']
        #repetitions = [1,3,10]
        #months = [1,3,11]
        #days = [1, 13, 25]
        #dates = []
    #for m in months:
            #for d in days:
                #dates.append(datetime.datetime(2007, m, d))
        
    def testCreateAlarmIndex1(self):
        # test alarm 5 min before
        result = createItems.createAlarmIndex('b0.5:100', [0,1,2,3], 
                                              [0,1,2,3,4,5], self.tzinfo)
        self.assertEqual(result, ({0: datetime.timedelta(-1, 86100), 
                                  1: datetime.timedelta(-1, 86100), 
                                  2: datetime.timedelta(-1, 86100), 
                                  3: datetime.timedelta(-1, 86100)}, 
                                  {}))
        
    def testCreateAlarmIndex2(self):
        # test alarm 5 min after
        result = createItems.createAlarmIndex('a0.5:100', [0,1,2,3], 
                                              [0,1,2,3,4,5], self.tzinfo)
        self.assertEqual(result, ({0: datetime.timedelta(0, 300), 
                                   1: datetime.timedelta(0, 300), 
                                   2: datetime.timedelta(0, 300), 
                                   3: datetime.timedelta(0, 300)}, 
                                   {}))
                                   
    def testCreateAlarmIndex3(self):
        # test custom alarm 5:05 PM 
        result = createItems.createAlarmIndex('c17.5:100', [0,1,2,3], 
                                              [0,1,2,3,4,5], self.tzinfo)
        self.assertEqual(result, ({}, 
                                {0: datetime.time(17, 5, 0, 0, self.tzinfo), 
                                1: datetime.time(17, 5, 0, 0, self.tzinfo), 
                                2: datetime.time(17, 5, 0, 0, self.tzinfo), 
                                3: datetime.time(17, 5, 0, 0, self.tzinfo), 
                                4: datetime.time(17, 5, 0, 0, self.tzinfo), 
                                5: datetime.time(17, 5, 0, 0, self.tzinfo)}))
        
    def testCreateAlarmIndex4(self):
        # test spec combining all types 
        result = createItems.createAlarmIndex('b0.5:30, a0.5:30, c17.5:40', 
                                              [1, 2, 3, 4, 5], 
                                              [1, 2, 3, 4, 5, 6, 7, 8, 9, 10], 
                                              self.tzinfo) 
        r0 = result[0].values()
        r0.sort()
        r1 = result[1].values()
        self.assertEqual(r0, [datetime.timedelta(-1, 86100), 
                              datetime.timedelta(0, 300)])
        self.assertEqual(r1, [datetime.time(17, 5, 0, 0,  self.tzinfo), 
                              datetime.time(17, 5, 0, 0,  self.tzinfo), 
                              datetime.time(17, 5, 0, 0,  self.tzinfo), 
                              datetime.time(17, 5, 0, 0,  self.tzinfo)])
        
    def testCreateStartTimeRange1(self):
        #test a spec where half the events start between 8AM-5PM and 
        #half start between 8PM-11PM
        result = createItems.createStartTimeRange('8-17:50, 18-23:50',
                                                  [1,2,3,4,5,6]).values()
        result.sort()
        self.assertEqual(result, [[8, 9, 10, 11, 12, 13, 14, 15, 16, 17], 
                                  [8, 9, 10, 11, 12, 13, 14, 15, 16, 17], 
                                  [8, 9, 10, 11, 12, 13, 14, 15, 16, 17], 
                                  [18, 19, 20, 21, 22, 23], 
                                  [18, 19, 20, 21, 22, 23], 
                                  [18, 19, 20, 21, 22, 23]])
                        
    #def testCreateAddressIndex(self):
        ##
        #createItems.createAddressIndex([1,2,3,4,5,6,7,8,9,10]
        #pass
    
    def testCreateItems(self):
        #test that an item gets created with the correct properties
        paramDict = {'choicePercentFYI': u'0', 
                     'choicePercentTentative': u'0',
                     'choicePercentMonthly': u'0', 
                     'textCtrlNoteSourceFilePath': u'itemGenNotes.txt', 
                     'textCtrlAlarmSpec': u'b0.10:100', 
                     'choicePercentNonRecurring': u'100', 
                     'choicePercentNow': u'100', 
                     'choicePercentAtTime': u'0',
                     'choicePercentDone': u'0', 
                     'choicePercentAnyTime': u'0', 
                     'choicePercentEvent': u'100', 
                     'textCtrlCollectionFileName': u'itemGenCollections.txt', 
                     'textCtrlTimeOfDay': u'8-8:100, 19-23:50', 
                     'choicePercentDaily': u'0', 
                     'textCtrlTitleSourceFile': u'itemGenTitles.txt', 
                     'textCtrlToFile': u'', 
                     'textCtrlRecurrenceEndDates': u'10:50, 0:50', 
                     'choicePercentTask': u'100', 
                     'textCtrlCCFileName': u'', 
                     'textCtrlEndDate': u'2008,1,2', 
                     'choicePercentConfirmed': u'100', 
                     'textCtrlTotalItems': u'1', 
                     'textCtrlToSpec': u'1:100', 
                     'textCtrlDuration': u'2.0:100', 
                     'choicePercentLater': u'0', 
                     'textCtrlStartDate': u'2008,1,1', 
                     'textCtrlCollectionCount': u'1', 
                     'textCtrlCollectionMembership':u'1:100',
                     'choicePercentYearly': u'0', 
                     'choicePercentAllDay': u'0', 
                     'textCtrlBCCSpec': u'0:100', 
                     'textCtrlCCSpec': u'0:100', 
                     'choicePercentUnassignedStatus': u'0', 
                     'choicePercentDuration': u'100', 
                     'textCtrlLocationSourceFilePath': u'itemGenLocations.txt', 
                     'choicePercentWeekly': u'0', 
                     'textCtrlBCCFileName': u'', 
                     'choicePercentMail': u'100', 
                     'choicePercentBiWeekly': u'0'}
        #create a single item with all stamps
        testItem = createItems.createItems(paramDict)[0]
        # test it has all stamps
        self.failUnless(pim.has_stamp(testItem, pim.mail.MailStamp))
        self.failUnless(pim.has_stamp(testItem, pim.TaskStamp))
        self.failUnless(pim.has_stamp(testItem, Calendar.EventStamp))
    
if __name__ == '__main__':
    unittest.main()
