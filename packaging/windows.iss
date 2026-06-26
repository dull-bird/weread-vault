#define AppVersion GetEnv("WEREAD_VAULT_VERSION")
#if AppVersion == ""
  #define AppVersion "0.0.0"
#endif

[Setup]
AppId={{D5F9B00D-82A1-4E5A-949B-36DD9D865703}
AppName=WeRead Vault
AppVersion={#AppVersion}
AppPublisher=dull-bird
AppPublisherURL=https://github.com/dull-bird/weread-vault
AppSupportURL=https://github.com/dull-bird/weread-vault/issues
AppUpdatesURL=https://github.com/dull-bird/weread-vault/releases/latest
DefaultDirName={localappdata}\Programs\WeRead Vault
DisableProgramGroupPage=yes
OutputDir=..\dist
OutputBaseFilename=weread-vault-windows-setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
UninstallDisplayIcon={app}\weread-vault.exe

[Files]
Source: "..\dist\weread-vault.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\WeRead Vault"; Filename: "{app}\weread-vault.exe"

[Run]
Filename: "{app}\weread-vault.exe"; Description: "启动 WeRead Vault"; Flags: nowait postinstall skipifsilent

[Code]
const
  EnvironmentKey = 'Environment';
  { 用 WV_ 前缀避免与 Inno Setup 6.7+ 内置的同名常量冲突（Duplicate identifier） }
  WV_HWND_BROADCAST = $FFFF;
  WV_WM_SETTINGCHANGE = $001A;
  WV_SMTO_ABORTIFHUNG = $0002;

function SendMessageTimeout(
  hWnd: LongWord; Msg: LongWord; wParam: LongWord; lParam: String;
  fuFlags: LongWord; uTimeout: LongWord; var lpdwResult: LongWord): LongWord;
  external 'SendMessageTimeoutW@user32.dll stdcall';

function PathContains(OldPath: String; Dir: String): Boolean;
begin
  Result := Pos(';' + Uppercase(Dir) + ';', ';' + Uppercase(OldPath) + ';') > 0;
end;

procedure BroadcastEnvironmentChange();
var
  ResultCode: LongWord;
begin
  SendMessageTimeout(WV_HWND_BROADCAST, WV_WM_SETTINGCHANGE, 0, 'Environment',
    WV_SMTO_ABORTIFHUNG, 5000, ResultCode);
end;

procedure AddToPath(Dir: String);
var
  OldPath: String;
  NewPath: String;
begin
  if not RegQueryStringValue(HKEY_CURRENT_USER, EnvironmentKey, 'Path', OldPath) then
    OldPath := '';

  if PathContains(OldPath, Dir) then
    exit;

  if OldPath = '' then
    NewPath := Dir
  else if Copy(OldPath, Length(OldPath), 1) = ';' then
    NewPath := OldPath + Dir
  else
    NewPath := OldPath + ';' + Dir;

  RegWriteStringValue(HKEY_CURRENT_USER, EnvironmentKey, 'Path', NewPath);
  BroadcastEnvironmentChange();
end;

procedure RemoveFromPath(Dir: String);
var
  OldPath: String;
  NewPath: String;
begin
  if not RegQueryStringValue(HKEY_CURRENT_USER, EnvironmentKey, 'Path', OldPath) then
    exit;

  NewPath := OldPath;
  StringChangeEx(NewPath, Dir + ';', '', True);
  StringChangeEx(NewPath, ';' + Dir, '', True);
  if CompareText(NewPath, Dir) = 0 then
    NewPath := '';

  if NewPath <> OldPath then begin
    RegWriteStringValue(HKEY_CURRENT_USER, EnvironmentKey, 'Path', NewPath);
    BroadcastEnvironmentChange();
  end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
    AddToPath(ExpandConstant('{app}'));
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  if CurUninstallStep = usPostUninstall then
    RemoveFromPath(ExpandConstant('{app}'));
end;
