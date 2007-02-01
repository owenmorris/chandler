#   Copyright (c) 2006-2007 Open Source Applications Foundation
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

import cosmoclient
import re
import ConfigParser
 
def getConfig():
   """Reads account information from config file"""
   """
   ## config file format must contain one entry for the root account like this:
   [admin] 
   user: username
   password: userpassword
   ##and a section for each user like this:
   [username]
   pw: password
   first: firstName
   last: lastName
   email: emailAdress
   """
   config = ConfigParser.ConfigParser()
   assert config.read('qasharing_accounts.ini'), 'Unable to read config file'
   global ADMIN_USER 
   global ADMIN_PASS
   global USER_ACCOUNTS
   ADMIN_USER = config.get('admin', 'user')
   ADMIN_PASS = config.get('admin', 'password')
   users = config.sections()
   users.remove('admin')
   USER_ACCOUNTS = []
   for sec in users:
      secDict = {'user':sec}
      for opt in config.options(sec):
         secDict[opt] = config.get(sec, opt)
      USER_ACCOUNTS.append(secDict)
   
def createAccounts():
   """
   Create accounts for testers and test scripts to use on qasharing cosmo box
   """
   SERVER_URL = r'http://qasharing.osafoundation.org:8080'
   getConfig()
   usersCreated = []
   
   #login as root
   client = cosmoclient.CosmoClient(SERVER_URL)
   client.set_basic_auth(ADMIN_USER, ADMIN_PASS)
   
   #Discover existing users
   p = re.compile('(?:<username>)(.*)(?:</username>)')
   def listExistingUsers():
      accountData = client.get(client._cmp_path+'/users')
      return p.findall(accountData, re.DOTALL)
   
   #create accounts
   existingUsers = listExistingUsers()
   for acc in USER_ACCOUNTS:
      user = acc['user']
      if user not in existingUsers:
         client.add_user(user, acc['pw'], acc['first'], acc['last'], acc['email'])
         assert client.response.status == 201
         usersCreated.append(user)
      else:
         print 'UserName %s already exists on cosmo server' % user
      
   #update existing users and verify accounts exist
   existingUsers = listExistingUsers()
   for user in usersCreated:
      assert user in existingUsers 
   
   #print account data (uncomment for debugging)
   #for x in accountData.split('\n'):
      #print x 
      

if __name__ == '__main__':
   createAccounts()
