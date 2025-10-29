# PostMini Installation Guide

## Windows Installation

### Download

Download the latest installer from the [releases page](https://github.com/yourusername/postmini/releases):
- `PostMini_Setup_v1.7.0.exe`

### Installation Steps

#### Handling Windows SmartScreen Warning

When you run the installer for the first time, Windows may show a security warning:

![Windows SmartScreen Warning](https://user-images.githubusercontent.com/example/smartscreen.png)

**This is normal and safe.** PostMini is not yet code-signed (we're working on it!). Here's how to install:

##### Method 1: Click "More info" (Recommended)

1. When you see "Windows protected your PC", click **"More info"**
2. A "Run anyway" button will appear at the bottom
3. Click **"Run anyway"**
4. The installer will start normally

![SmartScreen - More Info](https://user-images.githubusercontent.com/example/smartscreen-more-info.png)

##### Method 2: Unblock the file first

1. Right-click the downloaded installer file
2. Select **"Properties"**
3. At the bottom, check the **"Unblock"** checkbox
4. Click **"OK"**
5. Double-click the installer to run it normally

![Unblock File Properties](https://user-images.githubusercontent.com/example/unblock-file.png)

### Why does this happen?

Windows SmartScreen protects users by warning about applications that:
- Are not digitally signed with a code signing certificate
- Are from publishers without established reputation

PostMini is completely safe and open-source. You can:
- Review the [source code](https://github.com/yourusername/postmini)
- Check our [security policy](../README.md#security)
- See what data PostMini stores (all local, in `%APPDATA%\PostMini`)

**We're working on code signing to remove this warning in future releases.**

### Installer Options

Once the installer starts:

1. **Welcome Screen** - Shows version info and features
2. **License Agreement** - Read and accept the MIT license
3. **Installation Location** - Default: `C:\Program Files\PostMini`
   - Change if desired
4. **Desktop Icon** - Optional shortcut creation
5. **Install** - Begins installation
6. **Finish** - Launch PostMini

### First Launch

When you launch PostMini for the first time:

1. Choose your theme (Light/Dark)
2. Your data will be stored in: `C:\Users\YourName\AppData\Roaming\PostMini`
3. This includes:
   - Collections
   - Requests
   - Environments
   - History
   - Settings

All data is stored **locally on your computer** - nothing is sent to external servers.

## System Requirements

### Minimum Requirements
- **OS**: Windows 10 or later (64-bit)
- **RAM**: 4 GB
- **Disk Space**: 150 MB for application + space for data
- **Display**: 1024x768 resolution

### Recommended Requirements
- **OS**: Windows 11 (64-bit)
- **RAM**: 8 GB or more
- **Disk Space**: 500 MB
- **Display**: 1920x1080 resolution or higher

## Troubleshooting

### "Windows protected your PC" won't go away

Try these steps in order:

1. **Disable real-time protection temporarily** (Windows Security):
   - Open Windows Security
   - Go to "Virus & threat protection"
   - Click "Manage settings"
   - Turn off "Real-time protection" temporarily
   - Run the installer
   - Turn protection back on

2. **Use PowerShell to unblock**:
   ```powershell
   Unblock-File -Path "C:\path\to\PostMini_Setup_v1.7.0.exe"
   ```

3. **Check your antivirus**:
   - Some antivirus software may block unsigned applications
   - Add an exception for PostMini
   - Try disabling temporarily to install

### Installer fails to run

1. **Check you have administrator rights**
   - Right-click installer → "Run as administrator"

2. **Check disk space**
   - Ensure you have at least 150 MB free

3. **Check for corrupted download**
   - Re-download the installer
   - Verify the file size matches the release notes

### Application won't start after installation

1. **Check Windows Event Viewer**:
   - Press `Win + X` → Event Viewer
   - Look under "Windows Logs" → "Application"
   - Search for PostMini errors

2. **Missing Visual C++ Redistributables**:
   - Download and install [Microsoft Visual C++ Redistributable](https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist)

3. **Run in compatibility mode**:
   - Right-click PostMini.exe
   - Properties → Compatibility
   - Try "Windows 8" mode

### Data not persisting between sessions

Check that PostMini can write to:
```
C:\Users\YourName\AppData\Roaming\PostMini
```

If this folder doesn't exist or isn't writable:
1. Create it manually
2. Check folder permissions
3. Run PostMini as administrator once

## Updating PostMini

### Automatic Update (Planned for v1.8)

PostMini will check for updates automatically and prompt you to download.

### Manual Update

1. Download the latest installer
2. Run the installer - it will detect the existing installation
3. Choose to upgrade
4. Your data will be preserved (stored separately in AppData)

### Clean Installation

To completely remove and reinstall:

1. Uninstall from Windows Settings → Apps
2. Delete data folder: `C:\Users\YourName\AppData\Roaming\PostMini`
3. Install the new version

## Uninstalling PostMini

### Standard Uninstall

1. Open Windows Settings (Win + I)
2. Go to "Apps" → "Installed apps"
3. Find "PostMini"
4. Click "..." → "Uninstall"

**Note**: This removes the application but keeps your data safe in AppData.

### Complete Removal (Including Data)

After uninstalling the application:

1. Open File Explorer
2. Navigate to: `C:\Users\YourName\AppData\Roaming`
3. Delete the `PostMini` folder

**Warning**: This permanently deletes all your collections, requests, and settings.

## Data Backup

Before uninstalling or updating, you can backup your data:

### Using PostMini Export Feature

1. Open PostMini
2. Go to File → Export → Export All Collections
3. Save the JSON file somewhere safe
4. After reinstalling, use File → Import to restore

### Manual Backup

Copy this entire folder:
```
C:\Users\YourName\AppData\Roaming\PostMini
```

To restore, copy it back to the same location.

## Security & Privacy

### What data does PostMini collect?

**None.** PostMini:
- Stores all data locally on your computer
- Does not send telemetry or analytics
- Does not require an account or login
- Does not connect to any external services (except the APIs you test)

### Is PostMini open source?

Yes! You can:
- [View the source code](https://github.com/yourusername/postmini)
- Report security issues
- Contribute improvements
- Audit the code yourself

### Antivirus false positives

Some antivirus software may flag PostMini because:
- It's a new application without established reputation
- It makes network requests (that's its purpose!)
- It's built with PyInstaller (which some AV flags)

**PostMini is safe.** If your antivirus blocks it:
1. Add an exception for PostMini.exe
2. Report a false positive to your antivirus vendor
3. Check our [security policy](../README.md#security)

## Getting Help

### Documentation
- [User Guide](./guides/README.md)
- [Feature Guides](./guides/)
- [FAQ](../README.md#faq)

### Support
- [Report an issue](https://github.com/yourusername/postmini/issues)
- [Discussions](https://github.com/yourusername/postmini/discussions)
- Email: support@postmini.dev (if available)

### Community
- [GitHub Discussions](https://github.com/yourusername/postmini/discussions)
- [Discord](https://discord.gg/postmini) (if available)

## Known Issues

### Windows 11 Specific

- **High DPI scaling**: Some UI elements may appear blurry
  - Right-click PostMini.exe → Properties → Compatibility
  - Check "Override high DPI scaling"
  
### Windows 10 Specific

- **Theme detection**: Dark mode detection may not work
  - Manually set theme in Settings

## Next Steps

After installation:
1. Check out the [Quick Start Guide](./guides/V1.5.0_QUICK_REFERENCE.md)
2. Import a sample collection from `examples/`
3. Explore the [Feature Guides](./guides/)
4. Join the community!

---

**Questions or problems?** Open an issue on [GitHub](https://github.com/yourusername/postmini/issues).

