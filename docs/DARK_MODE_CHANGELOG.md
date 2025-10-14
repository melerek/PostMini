# Dark Mode Feature - v1.1

## What's New

🌙 **Dark Mode Toggle** - Instant theme switching with one click!

### Key Features

1. **Beautiful Dark Theme**
   - VS Code-inspired color palette
   - Professional design with excellent contrast
   - Easy on the eyes during long coding sessions

2. **One-Click Toggle**
   - 🌙 Moon button (light mode) → Click to go dark
   - ☀️ Sun button (dark mode) → Click to go light
   - Located in top-right corner of toolbar

3. **Persistent Preference**
   - Your theme choice is saved automatically
   - Loads your preferred theme on startup
   - Stored in `%APPDATA%/PostMini/settings.json`

4. **Instant Application**
   - No restart required
   - Applies to entire app immediately
   - Smooth transition between themes

## Files Changed

### New Files
- `styles_dark.qss` - Dark theme stylesheet
- `docs/DARK_MODE_GUIDE.md` - User guide
- `docs/DARK_MODE_SUMMARY.md` - Technical summary

### Modified Files
- `main.py` - Theme loading and persistence
- `src/ui/main_window.py` - Theme toggle UI
- `src/core/app_paths.py` - Settings file support (already had it)
- `README.md` - Updated features list
- `docs/POSTMINI_VS_POSTMAN_COMPARISON.md` - Updated comparison

## How to Use

1. **Open PostMini**
2. **Look for the theme button** in the top-right corner (🌙 or ☀️)
3. **Click to toggle** between light and dark themes
4. **Enjoy!** Your preference is saved automatically

## Benefits

✅ **Reduced eye strain** - Perfect for late-night coding  
✅ **Modern aesthetic** - Matches VS Code, IntelliJ, etc.  
✅ **Personal preference** - Choose what works best for you  
✅ **Professional look** - High-quality design  

## Technical Details

- **Theme storage**: `%APPDATA%/PostMini/settings.json`
- **Light theme**: `styles.qss`
- **Dark theme**: `styles_dark.qss`
- **Toggle method**: `MainWindow._toggle_theme()`

## Comparison with Postman

| Feature | PostMini v1.1 | Postman |
|---------|---------------|---------|
| Dark Mode | ✅ One-click toggle | ✅ Available |
| Theme Persistence | ✅ Automatic | ✅ Automatic |
| Theme Quality | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| Custom Themes | 🚧 Planned | ❌ |

## What's Next

Future enhancements planned:
- Multiple dark theme variants (AMOLED, Nord, Dracula)
- Keyboard shortcut for toggle
- Auto theme switching based on time
- Custom theme editor

## Feedback

Love the dark mode? Want more themes? Let us know!

---

**Version**: v1.1  
**Status**: ✅ Complete and Ready  
**Priority**: High (Top 3 feature gap with Postman)

