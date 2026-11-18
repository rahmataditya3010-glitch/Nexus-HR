[Setup]
AppName=NexusHR
AppVersion=1.0
DefaultDirName={autopf}\NexusHR
DefaultGroupName=NexusHR
OutputDir=installer_output
OutputBaseFilename=NexusHR_Setup
SetupIconFile=nexus.ico
UninstallDisplayIcon={app}\NexusHR.exe
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Tasks]
Name: "desktopicon"; Description: "Buat shortcut di Desktop"; GroupDescription: "Shortcut:"

[Files]
Source: "dist\NexusHR\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\NexusHR"; Filename: "{app}\NexusHR.exe"
Name: "{autodesktop}\NexusHR"; Filename: "{app}\NexusHR.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\NexusHR.exe"; Description: "Jalankan NexusHR"; Flags: nowait postinstall skipifsilent