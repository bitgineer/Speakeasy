; NSIS Installer Script for faster-whisper-hotkey
;
; This script creates a Windows installer with:
; - Welcome and license pages
; - Installation directory selection
; - Start menu shortcuts
; - Desktop shortcut (optional)
; - Auto-start on Windows startup (optional)
; - Uninstaller with cleanup options
;
; Usage:
;   "C:\Program Files (x86)\NSIS\makensis.exe" installer.nsi
;
; Output:
;   dist/faster-whisper-hotkey-setup-x.x.x.exe

!define APPNAME "faster-whisper-hotkey"
!define COMPANYNAME "blakkd"
!define DESCRIPTION "Push-to-talk transcription powered by cutting-edge ASR models"
!define VERSIONMAJOR 0
!define VERSIONMINOR 4
!define VERSIONBUILD 3
!define HELPURL "https://github.com/blakkd/faster-whisper-hotkey" ; Support URL
!define UPDATEURL "https://github.com/blakkd/faster-whisper-hotkey" ; Update URL
!define ABOUTURL "https://github.com/blakkd/faster-whisper-hotkey" ; About URL
!define INSTALLSIZE 500000 ; Estimated size in KB

!define DISTDIR "..\dist"
!define ICON_PATH "..\installer\app_icon.ico"
!define EXE_NAME "${APPNAME}.exe"

; Request admin privileges
RequestExecutionLevel admin

; Set compression
SetCompressor lzma
SetCompressorDictSize 64

; General settings
Name "${APPNAME}"
OutFile "${DISTDIR}\${APPNAME}-setup-${VERSIONMAJOR}.${VERSIONMINOR}.${VERSIONBUILD}.exe"
Unicode True
InstallDir "$PROGRAMFILES\${APPNAME}"
InstallDirRegKey HKCU "Software\${APPNAME}" ""

; Variables
Var StartMenuFolder
Var AutoStart
Var CreateDesktopIcon
Var DiskSpaceRequired
Var InstallErrorOccurred

; Interface settings
!include "MUI2.nsh"

!define MUI_ABORTWARNING
!define MUI_ICON "${ICON_PATH}"
!define MUI_UNICON "${ICON_PATH}"
!define MUI_HEADERIMAGE
!define MUI_HEADERIMAGE_BITMAP "${ICON_PATH}" ; Optional header image
!define MUI_WELCOMEFINISHPAGE_BITMAP "${ICON_PATH}" ; Optional welcome/finish image

; Pages
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "..\LICENSE.txt"
!insertmacro MUI_PAGE_COMPONENTS
!insertmacro MUI_PAGE_DIRECTORY

; Start Menu folder page
!define MUI_STARTMENUPAGE_DEFAULTFOLDER "${APPNAME}"
!define MUI_STARTMENUPAGE_REGISTRY_ROOT "HKCU"
!define MUI_STARTMENUPAGE_REGISTRY_KEY "Software\${APPNAME}"
!define MUI_STARTMENUPAGE_REGISTRY_VALUENAME "Start Menu Folder"
!insertmacro MUI_PAGE_STARTMENU Application $StartMenuFolder

; Custom page for options
Page custom OptionsPage OptionsPageLeave

!insertmacro MUI_PAGE_INSTFILES

; Finish page with run option
!define MUI_FINISHPAGE_RUN
!define MUI_FINISHPAGE_RUN_CHECKED
!define MUI_FINISHPAGE_RUN_TEXT "Launch ${APPNAME}"
!define MUI_FINISHPAGE_RUN_FUNCTION "LaunchApp"
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_WELCOME
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_UNPAGE_FINISH

; Languages
!insertmacro MUI_LANGUAGE "English"

; Error Handling Functions
Function .onInit
    ; Initialize variables
    StrCpy $InstallErrorOccurred "0"

    ; Check if already running
    System::Call 'kernel32::CreateMutexA(i 0, i 0, t "faster-whisper-hotkey-installer") i .r1 ?e'
    Pop $1
    ${If} $1 != 0
        MessageBox MB_OK|MB_ICONEXCLAMATION "The installer is already running."
        Abort
    ${EndIf}

    ; Check for Windows version (require Windows 10+)
    ${IfNot} ${AtLeastWin10}
        MessageBox MB_OK|MB_ICONSTOP "This application requires Windows 10 or later.$\n$\nYour Windows version is not supported."
        Abort
    ${EndIf}

    ; Check required disk space (500MB)
    StrCpy $DiskSpaceRequired 500000
    ${If} ${FileExists} "$INSTDIR\*.*"
        ; Check available disk space
        ${GetDrives} "HDD+" GetDriveFreeSpace
    ${EndIf}

FunctionEnd

Function GetDriveFreeSpace
    ; Get free space on drive
    ${DriveSpace} "$9  " $R0 $R1
    ${If} $R0 < $DiskSpaceRequired
        MessageBox MB_YESNO|MB_ICONEXCLAMATION "Warning: Less than ${DiskSpaceRequired} KB of disk space available on drive $9.$\n$\nDo you want to continue anyway?" IDYES +2
        Abort
    ${EndIf}
    Push $0
FunctionEnd

Function OptionsPageLeave
    ; Validate options before proceeding
    ${If} $InstallErrorOccurred == "1"
        MessageBox MB_OK|MB_ICONEXCLAMATION "An error occurred. Please try again."
        Abort
    ${EndIf}
FunctionEnd

; Installation Error Handler
Function CheckInstallError
    Pop $1  ; Get the error flag
    ${If} $1 != "0"
        StrCpy $InstallErrorOccurred "1"
        MessageBox MB_OK|MB_ICONEXCLAMATION "An error occurred during installation.$\n$\nError: $1"
    ${EndIf}
FunctionEnd

; Check for write permissions
Function CheckWritePermissions
    ; Try to create a test file in install directory
    GetTempFileName $0 $INSTDIR
    FileOpen $0 $0 "w"
    ${If} $0 == ""
        MessageBox MB_OK|MB_ICONEXCLAMATION "Cannot write to installation directory.$\n$\nPlease run the installer as Administrator."
        Return
    ${EndIf}
    FileClose $0
    Delete $0
FunctionEnd

; Installer Sections
Section "Main Application" SecMain

    SectionIn RO ; Required section

    ; Check write permissions before installing
    Call CheckWritePermissions

    ; Set output path
    SetOutPath $INSTDIR

    ; Copy main executable with error handling
    SetOverwrite try
    File "${DISTDIR}\${EXE_NAME}"
    ${If} ${FileExists} "$INSTDIR\${EXE_NAME}"
        DetailPrint "Main executable copied successfully"
    ${Else}
        MessageBox MB_OK|MB_ICONEXCLAMATION "Failed to copy main executable.$\n$\nPlease check disk space and permissions."
        Abort
    ${EndIf}

    ; Copy any additional files
    File /nonfatal "..\README.md"
    File /nonfatal "..\LICENSE.txt"

    ; Write uninstaller
    WriteUninstaller "$INSTDIR\uninstall.exe"

    ; Create registry keys for installation info
    WriteRegStr HKCU "Software\${APPNAME}" "Install_Dir" "$INSTDIR"
    WriteRegStr HKCU "Software\${APPNAME}" "Version" "${VERSIONMAJOR}.${VERSIONMINOR}.${VERSIONBUILD}"

    ; Add to Add/Remove Programs
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "DisplayName" "${APPNAME}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "UninstallString" "$INSTDIR\uninstall.exe"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "QuietUninstallString" "$INSTDIR\uninstall.exe /S"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "Publisher" "${COMPANYNAME}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "DisplayVersion" "${VERSIONMAJOR}.${VERSIONMINOR}.${VERSIONBUILD}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "HelpLink" "${HELPURL}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "URLUpdateInfo" "${UPDATEURL}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "URLInfoAbout" "${ABOUTURL}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "InstallLocation" "$INSTDIR"
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "EstimatedSize" ${INSTALLSIZE}
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "NoModify" 1
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "NoRepair" 1

    ; Create Start Menu shortcuts
    !insertmacro MUI_STARTMENU_WRITE_BEGIN Application
        CreateDirectory "$SMPROGRAMS\$StartMenuFolder"
        CreateShortcut "$SMPROGRAMS\$StartMenuFolder\${APPNAME}.lnk" "$INSTDIR\${EXE_NAME}" "" "$INSTDIR\${EXE_NAME}" 0 "" "${DESCRIPTION}"
        CreateShortcut "$SMPROGRAMS\$StartMenuFolder\Uninstall.lnk" "$INSTDIR\uninstall.exe"
    !insertmacro MUI_STARTMENU_WRITE_END

    ; Create Desktop shortcut if selected
    ${If} $CreateDesktopIcon == "1"
        CreateShortcut "$DESKTOP\${APPNAME}.lnk" "$INSTDIR\${EXE_NAME}" "" "$INSTDIR\${EXE_NAME}" 0 "" "${DESCRIPTION}"
    ${EndIf}

    ; Set up auto-start if selected
    ${If} $AutoStart == "1"
        CreateShortcut "$SMSTARTUP\${APPNAME}.lnk" "$INSTDIR\${EXE_NAME}" "" "$INSTDIR\${EXE_NAME}" 0 "" "${DESCRIPTION}"
    ${EndIf}

SectionEnd

; Options Page Function
Function OptionsPage

    ; Create custom page
    !insertmacro MUI_HEADER_TEXT "Installation Options" "Choose additional options"

    nsDialogs::Create 1018
    Pop $0

    ${NSD_CreateLabel} 0 0 100% 24u "Select additional installation options:"
    Pop $0

    ; Auto-start checkbox
    ${NSD_CreateCheckbox} 0 30u 100% 12u "Start ${APPNAME} automatically when Windows starts"
    Pop $AutoStart
    ${NSD_SetState} $AutoStart 0 ; Default unchecked

    ; Desktop icon checkbox
    ${NSD_CreateCheckbox} 0 50u 100% 12u "Create a desktop shortcut"
    Pop $CreateDesktopIcon
    ${NSD_SetState} $CreateDesktopIcon 1 ; Default checked

    nsDialogs::Show

FunctionEnd

Function OptionsPageLeave
    ; Nothing to validate, just save state
FunctionEnd

; Launch Application Function
Function LaunchApp
    ExecShell "" "$INSTDIR\${EXE_NAME}"
FunctionEnd

; Uninstaller Section
Section "Uninstall"

    ; Remove files
    Delete $INSTDIR\${EXE_NAME}
    Delete $INSTDIR\uninstall.exe
    Delete $INSTDIR\README.md
    Delete $INSTDIR\LICENSE.txt

    ; Remove shortcuts
    !insertmacro MUI_STARTMENU_GETFOLDER Application $StartMenuFolder

    Delete "$SMPROGRAMS\$StartMenuFolder\${APPNAME}.lnk"
    Delete "$SMPROGRAMS\$StartMenuFolder\Uninstall.lnk"
    RMDir "$SMPROGRAMS\$StartMenuFolder"

    Delete "$DESKTOP\${APPNAME}.lnk"
    Delete "$SMSTARTUP\${APPNAME}.lnk"

    ; Remove registry keys
    DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}"
    DeleteRegKey /ifempty HKCU "Software\${APPNAME}"

    ; Remove installation directory (if empty)
    RMDir $INSTDIR

    ; Ask about user data
    MessageBox MB_YESNO "Do you want to remove user data (settings, models, history)?" IDNO NoUserData
        ; Remove user data
        RMDir /r "$APPDATA\${APPNAME}"
        RMDir /r "$LOCALAPPDATA\${APPNAME}"
    NoUserData:

SectionEnd

; Section Descriptions
LangString DESC_SecMain ${LANG_ENGLISH} "The main application files."

!insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
    !insertmacro MUI_DESCRIPTION_TEXT ${SecMain} $(DESC_SecMain)
!insertmacro MUI_FUNCTION_DESCRIPTION_END
