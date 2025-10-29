# Code Signing Guide for PostMini

## Overview

This guide explains how to resolve Windows SmartScreen warnings ("Windows protected your PC") that appear when users install PostMini on Windows systems.

## The Problem

When users try to install `PostMini_Setup_v1.7.0.exe` on Windows, they may see:

```
Windows protected your PC
Microsoft Defender SmartScreen prevented an unrecognized app from starting.
Running this app might put your PC at risk.

App: PostMini_Setup_v17.0.exe
Publisher: Unknown publisher
```

**Why this happens:**
- The executable is not digitally signed with a code signing certificate
- Windows SmartScreen blocks unsigned apps from unknown publishers
- This is a security feature to protect users from malware

## Solutions

### Option 1: Code Signing (Recommended for Distribution)

Code signing provides the best user experience and builds trust.

#### What You Need:
1. **Code Signing Certificate** from a Certificate Authority (CA)
   - **Standard Certificates** (~$100-400/year):
     - Sectigo (formerly Comodo)
     - DigiCert
     - GlobalSign
   - **EV Certificates** (~$300-600/year):
     - Provides immediate SmartScreen reputation
     - Requires more verification
     - Stored on physical USB token

2. **SignTool** (part of Windows SDK)
   - Download: [Windows SDK](https://developer.microsoft.com/en-us/windows/downloads/windows-sdk/)

#### Steps to Sign Your Application:

##### 1. Obtain a Certificate

**For Standard Certificate:**
```powershell
# After purchasing, you'll receive a .pfx or .p12 file
# Store it securely with a strong password
```

**For EV Certificate:**
- Comes on a hardware USB token
- More secure, provides immediate reputation

##### 2. Sign the PyInstaller Executable

Add signing to your build process. Update `build_installer.spec`:

```python
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='PostMini',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,  # Leave None, we'll sign separately
    entitlements_file=None,
    icon='postmini_logo.ico',
)
```

##### 3. Create a Signing Script

Create `scripts/sign_executable.ps1`:

```powershell
# Sign PostMini Executable
param(
    [Parameter(Mandatory=$true)]
    [string]$CertPath,
    
    [Parameter(Mandatory=$true)]
    [string]$CertPassword,
    
    [string]$Timestamp = "http://timestamp.digicert.com"
)

$signTool = "C:\Program Files (x86)\Windows Kits\10\bin\10.0.22621.0\x64\signtool.exe"
$exePath = "dist\PostMini\PostMini.exe"

Write-Host "Signing $exePath..."

& $signTool sign `
    /f $CertPath `
    /p $CertPassword `
    /tr $Timestamp `
    /td SHA256 `
    /fd SHA256 `
    /d "PostMini - API Testing Tool" `
    /du "https://github.com/yourusername/postmini" `
    $exePath

if ($LASTEXITCODE -eq 0) {
    Write-Host "Successfully signed executable!" -ForegroundColor Green
} else {
    Write-Host "Failed to sign executable!" -ForegroundColor Red
    exit 1
}
```

##### 4. Sign the Installer

After building with Inno Setup, sign the installer:

Create `scripts/sign_installer.ps1`:

```powershell
# Sign PostMini Installer
param(
    [Parameter(Mandatory=$true)]
    [string]$CertPath,
    
    [Parameter(Mandatory=$true)]
    [string]$CertPassword,
    
    [string]$Version = "1.7.0",
    [string]$Timestamp = "http://timestamp.digicert.com"
)

$signTool = "C:\Program Files (x86)\Windows Kits\10\bin\10.0.22621.0\x64\signtool.exe"
$installerPath = "dist\installer\PostMini_Setup_v$Version.exe"

Write-Host "Signing $installerPath..."

& $signTool sign `
    /f $CertPath `
    /p $CertPassword `
    /tr $Timestamp `
    /td SHA256 `
    /fd SHA256 `
    /d "PostMini Setup" `
    /du "https://github.com/yourusername/postmini" `
    $installerPath

if ($LASTEXITCODE -eq 0) {
    Write-Host "Successfully signed installer!" -ForegroundColor Green
    
    # Verify the signature
    Write-Host "`nVerifying signature..."
    & $signTool verify /pa /v $installerPath
} else {
    Write-Host "Failed to sign installer!" -ForegroundColor Red
    exit 1
}
```

##### 5. Complete Build Process

Create `scripts/build_and_sign.ps1`:

```powershell
# Complete Build and Sign Process
param(
    [Parameter(Mandatory=$true)]
    [string]$CertPath,
    
    [Parameter(Mandatory=$true)]
    [string]$CertPassword,
    
    [string]$Version = "1.7.0"
)

Write-Host "=== Building PostMini v$Version ===" -ForegroundColor Cyan

# 1. Build with PyInstaller
Write-Host "`n[1/4] Building executable with PyInstaller..." -ForegroundColor Yellow
pyinstaller build_installer.spec --clean --noconfirm

if ($LASTEXITCODE -ne 0) {
    Write-Host "PyInstaller build failed!" -ForegroundColor Red
    exit 1
}

# 2. Sign the executable
Write-Host "`n[2/4] Signing executable..." -ForegroundColor Yellow
& .\scripts\sign_executable.ps1 -CertPath $CertPath -CertPassword $CertPassword

if ($LASTEXITCODE -ne 0) {
    Write-Host "Executable signing failed!" -ForegroundColor Red
    exit 1
}

# 3. Build installer with Inno Setup
Write-Host "`n[3/4] Building installer with Inno Setup..." -ForegroundColor Yellow
$innoSetup = "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
& $innoSetup installer.iss

if ($LASTEXITCODE -ne 0) {
    Write-Host "Inno Setup build failed!" -ForegroundColor Red
    exit 1
}

# 4. Sign the installer
Write-Host "`n[4/4] Signing installer..." -ForegroundColor Yellow
& .\scripts\sign_installer.ps1 -CertPath $CertPath -CertPassword $CertPassword -Version $Version

if ($LASTEXITCODE -ne 0) {
    Write-Host "Installer signing failed!" -ForegroundColor Red
    exit 1
}

Write-Host "`n=== Build Complete! ===" -ForegroundColor Green
Write-Host "Signed installer: dist\installer\PostMini_Setup_v$Version.exe" -ForegroundColor Green
```

##### 6. Usage

```powershell
# Store certificate path and password securely (e.g., environment variables)
$env:CERT_PATH = "C:\path\to\certificate.pfx"
$env:CERT_PASSWORD = "your-secure-password"

# Run the complete build
.\scripts\build_and_sign.ps1 -CertPath $env:CERT_PATH -CertPassword $env:CERT_PASSWORD
```

### Option 2: Self-Signed Certificate (Development/Testing Only)

**Note:** This won't remove SmartScreen warnings, but helps during development.

```powershell
# Create self-signed certificate (PowerShell as Administrator)
$cert = New-SelfSignedCertificate `
    -Subject "CN=PostMini Development" `
    -Type CodeSigning `
    -CertStoreLocation Cert:\CurrentUser\My

# Export certificate
Export-Certificate -Cert $cert -FilePath "postmini-dev.cer"

# Sign executable
$certPath = "Cert:\CurrentUser\My\$($cert.Thumbprint)"
Set-AuthenticodeSignature -FilePath "dist\PostMini\PostMini.exe" -Certificate $cert
```

### Option 3: Building SmartScreen Reputation (Long-term)

Even with a code signing certificate, new applications need to build reputation:

1. **Sign your application** (required)
2. **Distribute widely** - More downloads = better reputation
3. **Time** - Takes weeks/months to build reputation
4. **EV Certificate** - Provides immediate reputation (recommended)

### Option 4: User Workaround (Current State)

If you can't sign immediately, provide clear instructions to users:

**Installation Instructions for Windows SmartScreen:**

1. When you see "Windows protected your PC", click **"More info"**
2. Click **"Run anyway"** button
3. Follow the installer prompts

**Alternative method:**
1. Right-click the installer file
2. Select **Properties**
3. Check **"Unblock"** at the bottom
4. Click **OK**
5. Run the installer normally

## Recommended Certificates

### Budget-Friendly ($100-200/year)
- **Sectigo Code Signing**: ~$100/year
- **K Software Code Signing**: ~$84/year

### Premium ($300-600/year)
- **DigiCert EV Code Signing**: ~$600/year (immediate reputation)
- **Sectigo EV Code Signing**: ~$350/year (immediate reputation)

### Free (Not Recommended for Production)
- Let's Encrypt (doesn't offer code signing)
- Self-signed (users will still see warnings)

## Certificate Management Best Practices

1. **Store certificates securely**
   - Use environment variables for CI/CD
   - Never commit certificates to version control
   - Use hardware tokens for EV certificates

2. **Use timestamping**
   - Ensures signatures remain valid after certificate expires
   - Always use a timestamp server

3. **Verify signatures**
   - Check signatures after signing
   - Test on clean Windows machines

4. **Document the process**
   - Keep instructions for certificate renewal
   - Document the complete build and sign process

## Adding Certificate Info to Installer

Update `installer.iss` with certificate information:

```ini
[Setup]
AppPublisher=Your Company Name
AppPublisherURL=https://yourwebsite.com
SignTool=signtool
SignedUninstaller=yes
```

## Continuous Integration (CI/CD)

### GitHub Actions Example

Create `.github/workflows/build-and-sign.yml`:

```yaml
name: Build and Sign Release

on:
  push:
    tags:
      - 'v*'

jobs:
  build:
    runs-on: windows-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pyinstaller
    
    - name: Build executable
      run: pyinstaller build_installer.spec --clean --noconfirm
    
    - name: Import certificate
      run: |
        $pfxBytes = [System.Convert]::FromBase64String("${{ secrets.CERTIFICATE_BASE64 }}")
        [System.IO.File]::WriteAllBytes("cert.pfx", $pfxBytes)
    
    - name: Sign executable
      run: |
        & 'C:\Program Files (x86)\Windows Kits\10\bin\10.0.22621.0\x64\signtool.exe' sign `
          /f cert.pfx `
          /p "${{ secrets.CERTIFICATE_PASSWORD }}" `
          /tr http://timestamp.digicert.com `
          /td SHA256 `
          /fd SHA256 `
          dist\PostMini\PostMini.exe
    
    - name: Build installer
      run: |
        & 'C:\Program Files (x86)\Inno Setup 6\ISCC.exe' installer.iss
    
    - name: Sign installer
      run: |
        & 'C:\Program Files (x86)\Windows Kits\10\bin\10.0.22621.0\x64\signtool.exe' sign `
          /f cert.pfx `
          /p "${{ secrets.CERTIFICATE_PASSWORD }}" `
          /tr http://timestamp.digicert.com `
          /td SHA256 `
          /fd SHA256 `
          dist\installer\PostMini_Setup_*.exe
    
    - name: Upload release
      uses: actions/upload-artifact@v3
      with:
        name: PostMini-Installer
        path: dist\installer\PostMini_Setup_*.exe
```

## Resources

- [Microsoft Code Signing Guide](https://docs.microsoft.com/en-us/windows/win32/seccrypto/cryptography-tools)
- [SignTool Documentation](https://docs.microsoft.com/en-us/windows/win32/seccrypto/signtool)
- [Windows SmartScreen FAQ](https://docs.microsoft.com/en-us/windows/security/threat-protection/microsoft-defender-smartscreen/microsoft-defender-smartscreen-overview)
- [Code Signing Certificate Comparison](https://comodosslstore.com/code-signing)

## Summary

**Immediate Actions:**
1. Create a user guide explaining how to bypass SmartScreen (see below)
2. Add a note in your README about the SmartScreen warning

**Long-term Solution:**
1. Purchase a code signing certificate (EV recommended)
2. Implement the signing scripts
3. Sign both the executable and installer
4. Automate the process in your build pipeline

**Expected Timeline:**
- With standard certificate: 2-3 months to build reputation
- With EV certificate: Immediate reputation
- Cost: $100-600/year depending on certificate type

