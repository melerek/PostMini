# Windows SmartScreen - Quick Fix Guide

## The Issue

When installing PostMini on Windows, you may see this warning:

```
Windows protected your PC
Microsoft Defender SmartScreen prevented an unrecognized app from starting.
Running this app might put your PC at risk.

App: PostMini_Setup_v17.0.exe
Publisher: Unknown publisher
```

## Why Does This Happen?

Windows SmartScreen blocks applications that aren't digitally signed with a code signing certificate. This is a **security feature**, not a virus detection.

**PostMini is completely safe:**
- ✅ Open source code you can review
- ✅ No telemetry or data collection
- ✅ All data stored locally on your computer
- ✅ MIT Licensed

The warning appears simply because we haven't purchased a code signing certificate yet (they cost $300-600/year).

## Quick Fix (2 clicks)

### Step 1: Click "More info"

When you see the warning, click the **"More info"** link at the top:

```
Windows protected your PC
                           [More info]  ← Click here
Microsoft Defender SmartScreen prevented...
```

### Step 2: Click "Run anyway"

After clicking "More info", a button will appear:

```
Windows protected your PC

[Run anyway]  ← Click here
```

That's it! The installer will now run normally.

## Alternative Method: Unblock File First

If the above doesn't work, try this:

1. **Right-click** the downloaded `PostMini_Setup_v1.7.0.exe` file
2. Select **Properties**
3. At the bottom, check the **"Unblock"** checkbox:
   ```
   Security: This file came from another computer and might
   be blocked to help protect this computer.
   
   [✓] Unblock     [Apply]  [OK]
   ```
4. Click **Apply** and **OK**
5. Now double-click the installer - it should run without warning

## Still Having Issues?

### Temporary Disable Real-Time Protection

1. Open **Windows Security** (search in Start Menu)
2. Go to **"Virus & threat protection"**
3. Click **"Manage settings"**
4. Temporarily turn off **"Real-time protection"**
5. Run the installer
6. Turn protection back on immediately after

### Use PowerShell

Open PowerShell as Administrator and run:

```powershell
Unblock-File -Path "C:\path\to\PostMini_Setup_v1.7.0.exe"
```

(Replace the path with your actual download location)

## Is PostMini Safe?

**Yes, absolutely!** Here's why you can trust it:

1. **Open Source**: All code is publicly visible on GitHub
   - [View the source code](https://github.com/yourusername/postmini)
   
2. **No Data Collection**: PostMini doesn't:
   - Send telemetry or analytics
   - Require accounts or login
   - Connect to external servers (except the APIs you test)
   - Store data in the cloud
   
3. **Local Storage**: All your data stays on your computer:
   - Collections: `%APPDATA%\PostMini`
   - Nothing leaves your machine
   
4. **Transparent**: You can:
   - Audit the code yourself
   - Build from source
   - See exactly what data is stored where

## Why Not Just Sign It?

Good question! Code signing certificates cost $300-600/year for EV certificates (which provide immediate trust).

We're a free, open-source project, and we're working on:
1. Getting a certificate through sponsorships
2. Building a community to support the cost
3. In the meantime, users can bypass the warning safely

## Future Plans

We're working on getting a code signing certificate to remove this warning completely. Follow our progress:

- [GitHub Issue #XX](https://github.com/yourusername/postmini/issues/XX)
- Star the repo to show support
- Consider sponsoring to help cover certificate costs

## Related Resources

- [Full Installation Guide](USER_INSTALLATION_GUIDE.md) - Comprehensive setup instructions
- [Code Signing Guide](guides/CODE_SIGNING_GUIDE.md) - For developers who want to sign their builds
- [Security Policy](../README.md#security) - Our security practices

## Questions?

If you have concerns or questions:

1. **Review the code**: [GitHub Repository](https://github.com/yourusername/postmini)
2. **Ask the community**: [GitHub Discussions](https://github.com/yourusername/postmini/discussions)
3. **Report issues**: [GitHub Issues](https://github.com/yourusername/postmini/issues)

---

**TL;DR**: Click "More info" → "Run anyway". The warning is normal for unsigned apps. PostMini is safe and open-source.

