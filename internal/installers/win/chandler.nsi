  ;
  ; Chandler Win32 setup script
  ;
  ; $Revision$
  ; $Date$
  ; Copyright (c) 2004 Open Source Applications Founation
  ; http://osafoundation.org/Chandler_0.1_license_terms.htm
  ;

!define PRODUCT_NAME "Chandler"
!define PRODUCT_VERSION "0.4+"
!define PRODUCT_PUBLISHER "Open Source Application Foundation"
!define PRODUCT_WEB_SITE "http://www.osafoundation.org"
!define PRODUCT_DIR_REGKEY "Software\Microsoft\Windows\CurrentVersion\App Paths\chandlerDebug.exe"
!define PRODUCT_UNINST_KEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}"
!define PRODUCT_UNINST_ROOT_KEY "HKLM"

; MUI 1.67 compatible ------
!include "MUI.nsh"

; MUI Settings
!define MUI_ABORTWARNING
!define MUI_ICON "${NSISDIR}\Contrib\Graphics\Icons\modern-install.ico"
!define MUI_UNICON "${NSISDIR}\Contrib\Graphics\Icons\modern-uninstall.ico"

; Language Selection Dialog Settings
!define MUI_LANGDLL_REGISTRY_ROOT "${PRODUCT_UNINST_ROOT_KEY}"
!define MUI_LANGDLL_REGISTRY_KEY "${PRODUCT_UNINST_KEY}"
!define MUI_LANGDLL_REGISTRY_VALUENAME "NSIS:Language"

; Wizard pages
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "Chandler\LICENSE.txt"
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES

!define MUI_FINISHPAGE_RUN "$INSTDIR\chandlerDebug.exe"
!define MUI_FINISHPAGE_SHOWREADME "$INSTDIR\README.win.txt"
!insertmacro MUI_PAGE_FINISH

; Uninstaller pages
!insertmacro MUI_UNPAGE_INSTFILES

; Language files
!insertmacro MUI_LANGUAGE "English"
!insertmacro MUI_LANGUAGE "French"
!insertmacro MUI_LANGUAGE "German"
!insertmacro MUI_LANGUAGE "Japanese"
!insertmacro MUI_LANGUAGE "Spanish"

; MUI end ------

Name "${PRODUCT_NAME} ${PRODUCT_VERSION}"
OutFile "Setup.exe"
InstallDir "$PROGRAMFILES\Chandler"
InstallDirRegKey HKLM "${PRODUCT_DIR_REGKEY}" ""
ShowInstDetails nevershow
ShowUnInstDetails nevershow

Section "MainSection" SEC01
  SetOutPath "$INSTDIR"
  File "Chandler\*.*"
  
    ; this could be handled completely by the above line
    ; if the /r option was used - I kept them as individual
    ; items to better document what sub-folders are included
    
  File /r "Chandler\application"
  File /r "Chandler\crypto"
  File /r "Chandler\debug"
  File /r "Chandler\locale"
  File /r "Chandler\parcels"
  File /r "Chandler\repository"
  File /r "Chandler\tools"

  CreateDirectory "$SMPROGRAMS\Chandler"
  CreateShortCut "$SMPROGRAMS\Chandler\Chandler.lnk" "$INSTDIR\chandlerDebug.exe"
  CreateShortCut "$DESKTOP\Chandler.lnk" "$INSTDIR\chandlerDebug.exe"
SectionEnd

  ; create the uninstall shortcut - done here so that it will only
  ; be created *if* the install was successful
  
Section -AdditionalIcons
  CreateShortCut "$SMPROGRAMS\Chandler\Uninstall.lnk" "$INSTDIR\uninst.exe"
SectionEnd

  ; post install steps - add Chandler to the add/remove programs registry list
  
Section -Post
  WriteUninstaller "$INSTDIR\uninst.exe"
  WriteRegStr HKLM "${PRODUCT_DIR_REGKEY}" "" "$INSTDIR\chandlerDebug.exe"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayName" "$(^Name)"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "UninstallString" "$INSTDIR\uninst.exe"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayIcon" "$INSTDIR\chandlerDebug.exe"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayVersion" "${PRODUCT_VERSION}"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "URLInfoAbout" "${PRODUCT_WEB_SITE}"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "Publisher" "${PRODUCT_PUBLISHER}"
SectionEnd

Function un.onUninstSuccess
  HideWindow
  MessageBox MB_ICONINFORMATION|MB_OK "$(^Name) was successfully removed from your computer."
FunctionEnd

Function un.onInit
!insertmacro MUI_UNGETLANGUAGE
  MessageBox MB_ICONQUESTION|MB_YESNO|MB_DEFBUTTON2 "Are you sure you want to completely remove $(^Name) and all of its components?" IDYES +2
  Abort
FunctionEnd

  ; this section controls exactly what parts of Chandler are removed
  ; currently *all* directories are removed

Section Uninstall
  Delete "$INSTDIR\uninst.exe"
  Delete "$SMPROGRAMS\Chandler\Uninstall.lnk"
  Delete "$DESKTOP\Chandler.lnk"
  Delete "$SMPROGRAMS\Chandler\Chandler.lnk"

    ; currently commented out to prevent testing blow-outs ;)
  ;Delete "$INSTDIR\*.*"
  Delete "$INSTDIR\Chandler.py"
  Delete "$INSTDIR\ChangeLog.txt"
  Delete "$INSTDIR\HISTORY.txt"
  Delete "$INSTDIR\LICENSE.txt"
  Delete "$INSTDIR\setup.py"
  Delete "$INSTDIR\version.py"

  RMDir "$SMPROGRAMS\Chandler"

  RMDir /r "$INSTDIR\application"
  RMDir /r "$INSTDIR\crypto"
  RMDir /r "$INSTDIR\debug"
  RMDir /r "$INSTDIR\locale"
  RMDir /r "$INSTDIR\parcels"
  RMDir /r "$INSTDIR\repository"
  RMDir /r "$INSTDIR\tools"
  RMDir /r "$INSTDIR\__repository__"

    ; currently commented out to prevent testing blow-outs ;)
  ;RMDir "$INSTDIR"

  DeleteRegKey ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}"
  DeleteRegKey HKLM "${PRODUCT_DIR_REGKEY}"
  SetAutoClose true
SectionEnd
