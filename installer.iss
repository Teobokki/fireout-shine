#define MyVer "1.0.5"
[Setup]
AppId={{7E3A91C4-2B6D-4F18-A5C9-3D8E1F0B6A72}
AppName=FIREOUT SHINE
AppVersion={#MyVer}
AppVerName=FIREOUT SHINE {#MyVer}
AppPublisher=EX Inc./HYPERION DIGITAL
AppPublisherURL=https://github.com/Teobokki/fireout-shine
AppCopyright=©2026 EX Inc./HYPERION DIGITAL ©2026
VersionInfoVersion={#MyVer}
VersionInfoCompany=EX Inc./HYPERION DIGITAL
VersionInfoCopyright=©2026 EX Inc./HYPERION DIGITAL ©2026
VersionInfoProductName=FIREOUT SHINE
VersionInfoDescription=FIREOUT SHINE Setup
DefaultDirName={localappdata}\Programs\FIREOUT SHINE
DefaultGroupName=FIREOUT SHINE
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=dist
OutputBaseFilename=FIREOUT-SHINE-Setup-{#MyVer}
SetupIconFile=assets\icon.ico
UninstallDisplayIcon={app}\FIREOUT SHINE.exe
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
CloseApplications=yes

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[InstallDelete]
Type: filesandordirs; Name: "{app}\_internal"

[Files]
Source: "dist\FIREOUT SHINE\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\FIREOUT SHINE"; Filename: "{app}\FIREOUT SHINE.exe"
Name: "{group}\Uninstall FIREOUT SHINE"; Filename: "{uninstallexe}"
Name: "{userdesktop}\FIREOUT SHINE"; Filename: "{app}\FIREOUT SHINE.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\FIREOUT SHINE.exe"; Description: "Launch FIREOUT SHINE now"; Flags: nowait postinstall skipifsilent
