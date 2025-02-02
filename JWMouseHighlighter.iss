[Setup]
AppName=JW Mouse Highlighter
AppVersion=1.0
DefaultDirName={pf}\JW Mouse Highlighter
DefaultGroupName=JW Mouse Highlighter
OutputDir=.
OutputBaseFilename=JW_Mouse_Highlighter_Installer
UninstallDisplayIcon={app}\jwmousehighlighter.exe

[Files]
Source: "jwmousehighlighter.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "icon.png"; DestDir: "{app}"; Flags: ignoreversion
Source: "icon.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\JW Mouse Highlighter"; Filename: "{app}\jwmousehighlighter.exe"
Name: "{commondesktop}\JW Mouse Highlighter"; Filename: "{app}\jwmousehighlighter.exe"

[Run]
Filename: "{app}\jwmousehighlighter.exe"; Description: "Launch JW Mouse Highlighter"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: files; Name: "{app}\jwmousehighlighter.exe"
Type: files; Name: "{app}\icon.png"
Type: files; Name: "{app}\icon.ico"