# PostMini v1.9.6 - Consolidated Notification System

## 🎨 UI/UX Enhancements

### 🔔 Consolidated Notification System
We've completely redesigned how PostMini communicates with users by removing popup toast notifications and consolidating everything into the status bar.

**Key Improvements:**
- **✅ Cleaner Interface** - No more popup toasts cluttering your workspace
- **🎨 Color-Coded Messages** - Instant visual feedback with color-coded status:
  - 🟢 **Green** (#4CAF50) for success messages
  - 🔴 **Red** (#F44336) for error messages  
  - 🟠 **Orange** (#FF9800) for warning messages
  - 🔵 **Blue** (#2196F3) for informational messages
- **⏱️ Auto-Reset** - Messages automatically reset to "Ready" after 5 seconds
- **📊 Less Intrusive** - Focus on your work without popup distractions
- **🔄 Consistent** - Single notification method throughout the entire application

### 🔧 Technical Improvements
- Removed ToastManager and ToastNotification widgets from codebase
- Consolidated 90+ notification calls to use unified `_show_status()` method
- Simplified notification architecture for better maintainability

---

## 📥 Installation

### Windows Installer
**Download:** [PostMini_Setup_v1.9.6.exe](https://github.com/melerek/PostMini/releases/download/v1.9.6/PostMini_Setup_v1.9.6.exe)

### Checksums
- **Installer SHA256:** `9356A60138717FB800F46B21644F0C9667753D65ADCEF239D18579E02776589C`
- **Executable SHA256:** `A2D6A4757521EFED82BEF1A9E320584CD05A904A3F57F3182E6F9D532E512D1A`

### Verification
```powershell
# Verify installer
Get-FileHash -Path "PostMini_Setup_v1.9.6.exe" -Algorithm SHA256

# Verify executable (after installation)
Get-FileHash -Path "C:\Program Files\PostMini\PostMini.exe" -Algorithm SHA256
```

---

## 🚀 What's Next

PostMini continues to evolve as a privacy-focused, Git-based alternative to Postman. Stay tuned for more features and improvements!

**Full Changelog:** [CHANGELOG.md](https://github.com/melerek/PostMini/blob/main/CHANGELOG.md)
