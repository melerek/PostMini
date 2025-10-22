# PostMini Windows Installer - User Guide

This guide explains how to install, use, and uninstall PostMini on Windows using the installer.

---

## 📦 Installing PostMini

### System Requirements

- **Operating System:** Windows 10 or later (64-bit)
- **Disk Space:** ~150 MB for installation
- **Memory:** 4 GB RAM minimum
- **Administrator Rights:** Not required (installs per-user by default)

### Installation Steps

1. **Download the Installer:**
   - Get `PostMini_Setup_v1.0.0.exe` from the [Releases page](https://github.com/yourusername/postmini/releases)
   - Save it to your Downloads folder

2. **Run the Installer:**
   - Double-click `PostMini_Setup_v1.0.0.exe`
   - If Windows SmartScreen appears, click "More info" → "Run anyway"
   - The installer wizard will open

3. **Follow the Wizard:**
   - **Welcome Screen:** Click "Next"
   - **License Agreement:** Review and click "I accept"
   - **Installation Location:** Default is `C:\Program Files\PostMini\` (you can change this)
   - **Select Components:** Choose whether to create desktop/quick launch icons
   - **Install:** Click "Install" to begin

4. **Complete Installation:**
   - Wait for files to copy (~1 minute)
   - Check "Launch PostMini" if you want to start immediately
   - Click "Finish"

### What Gets Installed

**Program Files** (in `C:\Program Files\PostMini\`):
```
PostMini/
├── PostMini.exe          # Main application
├── _internal/            # Python runtime & dependencies
├── docs/                 # Documentation
├── styles.qss            # Stylesheet
└── README.md
```

**User Data** (in `%APPDATA%\PostMini\`):
```
C:\Users\<YourName>\AppData\Roaming\PostMini\
├── api_client.db         # Your collections and requests
├── logs/                 # Application logs
└── exports/              # Exported collections
```

**Start Menu:**
- `PostMini` shortcut added to All Programs

**Desktop (optional):**
- `PostMini` shortcut

---

## 🚀 First Launch

When you first launch PostMini:

1. **Initial Setup:**
   - PostMini automatically creates the data directory in `%APPDATA%\PostMini\`
   - A new database file is created for your collections
   - You'll see an empty main window

2. **Verify Installation:**
   - Look at the console output (if visible) for: `Application data directory: C:\Users\<You>\AppData\Roaming\PostMini`
   - This confirms your data is being stored correctly

3. **Start Using PostMini:**
   - Create your first collection
   - Add requests
   - All data is automatically saved

---

## 📁 Data Storage

### User Data Location

**All your data is stored in:**
```
%APPDATA%\PostMini\
```

Or expanded:
```
C:\Users\<YourUsername>\AppData\Roaming\PostMini\
```

### Why %APPDATA%?

✅ **Safe from Permission Issues:** User data folder doesn't require admin rights  
✅ **Preserved During Updates:** Program Files are overwritten, but %APPDATA% is kept  
✅ **Standard Windows Practice:** All modern apps use AppData for user data  
✅ **Easy Backup:** Just copy the PostMini folder to backup everything  

### What's Stored Where

| Data Type | Location | Description |
|-----------|----------|-------------|
| Collections & Requests | `%APPDATA%\PostMini\api_client.db` | SQLite database |
| Application Logs | `%APPDATA%\PostMini\logs\` | Error logs and diagnostics |
| Exported Collections | `%APPDATA%\PostMini\exports\` | JSON export files |
| Git Sync Files | Your project directory | `.postmini/` and `.postmini-secrets/` |

---

## 🔄 Updating PostMini

### How Updates Work

1. **Download New Installer:** Get the latest `PostMini_Setup_vX.X.X.exe`
2. **Run Installer:** It will detect the existing installation
3. **Automatic Upgrade:** 
   - Old program files are replaced
   - **Your data in %APPDATA% is preserved**
   - Settings and collections remain intact
4. **Launch:** Your data is still there!

### Manual Update Steps

1. **(Optional) Backup Your Data:**
   ```
   Copy: %APPDATA%\PostMini\
   To: Desktop\PostMini_Backup\
   ```

2. **Close PostMini** if it's running

3. **Run New Installer:** Follow the same installation steps

4. **Launch PostMini:** Everything should be as you left it

---

## 🗑️ Uninstalling PostMini

### Standard Uninstall

1. **Open Windows Settings:**
   - Press `Win + I`
   - Go to "Apps" → "Apps & features"

2. **Find PostMini:**
   - Search for "PostMini" in the list
   - Click on it

3. **Uninstall:**
   - Click "Uninstall"
   - Confirm when prompted
   - The uninstaller will run

4. **Data Choice:**
   - Program files in `C:\Program Files\PostMini\` are removed
   - **Your data in %APPDATA% is NOT removed** (preserved for reinstallation)

### Complete Removal (Including Data)

If you want to completely remove PostMini including all data:

1. **Uninstall via Windows Settings** (see above)

2. **Manually Delete User Data:**
   - Press `Win + R`
   - Type: `%APPDATA%`
   - Press Enter
   - Find and delete the `PostMini` folder

3. **(Optional) Remove Start Menu Shortcuts:**
   - These are usually removed automatically
   - Check: `%APPDATA%\Microsoft\Windows\Start Menu\Programs\`

---

## 🔧 Troubleshooting

### PostMini Won't Start

**Symptom:** Double-clicking the icon does nothing, or the app crashes immediately.

**Solutions:**
1. Check Task Manager for hung `PostMini.exe` processes
2. Try running as administrator (right-click → "Run as administrator")
3. Check event logs: `%APPDATA%\PostMini\logs\`
4. Reinstall PostMini

### "Database is Locked" Error

**Cause:** Another instance of PostMini is running.

**Solution:**
1. Check system tray for PostMini icon
2. Open Task Manager (`Ctrl+Shift+Esc`)
3. Look for `PostMini.exe` under Processes
4. End all PostMini processes
5. Restart PostMini

### Can't Find My Data

**Verify Data Location:**
1. Press `Win + R`
2. Type: `%APPDATA%\PostMini`
3. Press Enter
4. You should see `api_client.db` and other folders

If the folder doesn't exist, PostMini hasn't been run yet, or there was an error during first launch.

### Antivirus Blocking PostMini

**Symptom:** Antivirus flags `PostMini.exe` as suspicious.

**Why:** PyInstaller executables can trigger false positives.

**Solution:**
1. Add exception for `C:\Program Files\PostMini\PostMini.exe`
2. Verify the installer was downloaded from official sources
3. Scan with VirusTotal if concerned (should be clean)

### Installer Won't Run

**Symptom:** Windows SmartScreen blocks the installer.

**Solution:**
1. Click "More info"
2. Click "Run anyway"
3. This is normal for unsigned installers

**For IT Admins:** Consider code-signing the executable for enterprise deployment.

### Permission Errors

**Symptom:** "Access denied" errors when saving data.

**Cause:** Trying to write to Program Files instead of %APPDATA%.

**Solution:**
1. Make sure you're using the installed version (not running from Downloads)
2. Verify data directory in app: Look for "Application data directory" in console output
3. Reinstall if problem persists

---

## 🔒 Security & Privacy

### What Data is Collected?

**PostMini does NOT:**
- ❌ Send any data to external servers
- ❌ Track your usage
- ❌ Require an account or login
- ❌ Connect to the internet except for your API requests

**PostMini ONLY:**
- ✅ Stores data locally on your computer
- ✅ Makes HTTP requests that YOU initiate
- ✅ Logs errors locally for debugging

### Is My Data Safe?

- ✅ **Local Storage Only:** Everything stays on your computer
- ✅ **No Cloud Sync:** No automatic uploads to any service
- ✅ **Your Control:** You decide what to share via Git
- ✅ **Secrets Management:** API keys can be gitignored
- ✅ **Standard Practices:** Uses Windows standard data locations

### Network Access

PostMini requires internet access only for:
- Making API requests to the URLs you specify
- OAuth authentication flows (if you use OAuth features)

No other network activity occurs.

---

## 💡 Tips & Best Practices

### Backup Your Data

**Manual Backup:**
```
Copy: %APPDATA%\PostMini\
To: Your backup location
```

**Git Backup:**
- Use the Git Sync feature to version control your collections
- Push to a private repository for cloud backup

### Share PostMini with Team

1. **Share the Installer:** Send `PostMini_Setup_vX.X.X.exe` to teammates
2. **Use Git Sync:** Version control collections for team collaboration
3. **Document APIs:** Use collection descriptions to document your APIs

### Performance Tips

- **Large Collections:** Export/import collections in smaller chunks
- **Slow Response Times:** Check your internet connection
- **High CPU Usage:** Close unused collections, restart PostMini

---

## 📞 Support

### Getting Help

- **Documentation:** `C:\Program Files\PostMini\docs\index.html`
- **GitHub Issues:** [Report bugs or request features](https://github.com/yourusername/postmini/issues)
- **Community:** [Discussions page](https://github.com/yourusername/postmini/discussions)

### Before Reporting Issues

1. Check this troubleshooting guide
2. Verify you're using the latest version
3. Check logs in `%APPDATA%\PostMini\logs\`
4. Try reinstalling PostMini

---

## 🎉 Enjoy PostMini!

You're all set! Start building and testing your APIs with PostMini.

**Quick Links:**
- [User Guide](index.html) - Complete feature documentation
- [Git Sync Guide](GIT_SYNC_GUIDE.md) - Team collaboration
- [Keyboard Shortcuts](#) - Speed up your workflow

---

**Version:** 1.0.0  
**Last Updated:** October 2025

