; Inno Setup Script for PostMini Installer
; This script creates a Windows installer for the PostMini application

#define MyAppName "PostMini"
#define MyAppVersion "2.0.1"
#define MyAppPublisher "PostMini"
#define MyAppURL "https://github.com/yourusername/postmini"
#define MyAppExeName "PostMini.exe"

[Setup]
; Basic app information
AppId={{A8B9C7D6-E5F4-4321-9876-543210FEDCBA}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DisableProgramGroupPage=yes
LicenseFile=LICENSE.txt
; Uncomment the following line to run in non administrative install mode (install for current user only.)
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
OutputDir=dist\installer
OutputBaseFilename=PostMini_Setup_v{#MyAppVersion}
; SetupIconFile=resources\icon.ico  ; Commented out - no icon file yet
Compression=lzma
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked; OnlyBelowVersion: 6.1; Check: not IsAdminInstallMode

[Files]
; Main executable and all dependencies from PyInstaller output
Source: "dist\PostMini\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; Essential documentation only (README, LICENSE, CHANGELOG)
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "LICENSE.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "CHANGELOG.md"; DestDir: "{app}"; Flags: ignoreversion
; NOTE: Full documentation available at https://github.com/melerek/PostMini

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: quicklaunchicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[Code]
procedure InitializeWizard;
var
  WelcomeLabel: TNewStaticText;
begin
  WelcomeLabel := TNewStaticText.Create(WizardForm);
  WelcomeLabel.Parent := WizardForm.WelcomePage;
  WelcomeLabel.Caption :=
    'PostMini v1.8.5 - Professional API Testing Tool' + #13#10 + #13#10 +
    'NEW in v1.8.5:' + #13#10 +
    '  • NEW: Automatic update system' + #13#10 +
    '  • Check for updates from Settings panel' + #13#10 +
    '  • Auto-check on startup (configurable)' + #13#10 +
    '  • One-click download and install updates' + #13#10 +
    '  • Version display in Settings' + #13#10 +
    '  • Background download with progress tracking' + #13#10 + #13#10 +
    'Also includes v1.8.3 fixes:' + #13#10 +
    '  • Postman folder structure import fixed' + #13#10 + #13#10 +
    'Your data will be stored locally in:' + #13#10 +
    ExpandConstant('{userappdata}\PostMini') + #13#10 + #13#10 +
    'This ensures your collections and settings are preserved across updates.';
  WelcomeLabel.AutoSize := True;
  WelcomeLabel.WordWrap := True;
  WelcomeLabel.Top := WizardForm.WelcomeLabel2.Top + WizardForm.WelcomeLabel2.Height + 20;
end;

function InitializeSetup(): Boolean;
var
  ResultCode: Integer;
begin
  // Check if application is already running
  if CheckForMutexes('PostMiniSingleInstance') then
  begin
    if MsgBox('PostMini is currently running. Please close it before continuing setup.' + #13#10#13#10 + 
              'Would you like to close it now?', 
              mbConfirmation, MB_YESNO) = IDYES then
    begin
      // Attempt to close the application gracefully
      Exec('taskkill.exe', '/IM PostMini.exe /F', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
      Sleep(1000);
    end
    else
    begin
      Result := False;
      Exit;
    end;
  end;
  Result := True;
end;

[UninstallDelete]
Type: filesandordirs; Name: "{app}\logs"

