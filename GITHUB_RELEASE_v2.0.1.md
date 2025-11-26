# PostMini v2.0.1 - Selective Git Sync

## 🌐🔒 Major New Feature: Selective Git Sync

**Choose what to sync with your team!** Collections and environments can now be marked as "Public" (synced to Git) or "Private" (local only), enabling personal workspace organization alongside team collaboration.

### Key Capabilities

- **🌐 Public (Sync to Git)**: Share with your team via Git - perfect for shared API collections, staging/production environments
- **🔒 Private (Local Only)**: Keep personal collections/environments private - ideal for experimental work, personal scripts
- **🔐 Secret Variables**: Mark sensitive environment variables (API keys, tokens, passwords) as secrets - stored locally only, never committed to Git
- **Visual Indicators**: See sync status at a glance with 🌐 (public) and 🔒 (private) icons
- **Automatic Git Integration**: Making something public automatically exports to `.postmini/` folder; making private automatically removes the file
- **Easy Toggle**: Right-click context menu on collections, or "Make Public/Private" button on environments

### How It Works

1. **Collections**: Right-click any collection → "Make Public (Sync to Git)" - file is auto-created in `.postmini/collections/`
2. **Collections**: Right-click public collection → "Make Private (Don't Sync)" - file is auto-removed from Git folder
3. **Environments**: Click "Make Public" button on environment card - file is auto-created in `.postmini/environments/`
4. **Environments**: Click "Make Private" button - file is auto-removed from Git folder
5. **Secret Variables**: Right-click any environment variable in Variables Inspector → "Mark as Secret" - value is masked with ●●●●●●●●
6. **GitSync**: Only public items are exported when you push to Git - private items and secrets are excluded automatically

### Full Feature Set

✅ **Backend**: Database schema (`sync_to_git` column), export/import filtering, secret tracking  
✅ **Collections UI**: 🌐/🔒 icons in tree, context menu toggle with auto-export/cleanup  
✅ **Environments UI**: 🌐/🔒 icons on cards, "Make Public/Private" buttons with auto-export/cleanup  
✅ **Secret Variables UI**: 🔐 icon, masked values (●●●●●●●●), "Mark as Secret/Regular" context menu  
✅ **Variables Inspector**: TYPE column with sync/secret icons  
✅ **Git Sync Dialog**: Modern styling, public/private/secret counts in status panel  
✅ **Automatic File Management**: Toggle triggers instant export/cleanup  

## 🐛 Bug Fixes

### GitSync Status Detection
- **Fixed persistent "import available" status**: GitSync now correctly compares file content with database instead of relying on in-memory hashes cleared on restart
- **Fixed false "modified" detection**: Comparison now excludes `export_date` timestamp that changes on every export
- **Fixed conflict detection**: Now only checks public collections/environments instead of flagging private items as conflicts

### UI/UX Improvements
- **Fixed transparent menu text**: Environment context menus now have proper styling for both dark and light themes
- **Fixed unnecessary scrolling**: Environments list now expands to fill available space
- **Improved menu button styling**: "⋯" menu button on environment cards has consistent theming

## 🔧 Technical Improvements

- Replaced in-memory hash-based change detection with real-time content comparison
- Added `remove_collection_file()` and `remove_environment_file()` methods for automatic cleanup
- Updated toggle handlers to call auto-sync for export and auto-cleanup for removal
- Fixed `detect_changes()` to only compare public collections/environments against files

## 📥 Installation

**Download**: [PostMini_Setup_v2.0.1.exe](https://github.com/melerek/PostMini/releases/download/v2.0.1/PostMini_Setup_v2.0.1.exe)

**Checksums**:
- Installer SHA256: `08F890DE4A02BD05DEE31861785DFE6BBA5DA8A2903BC8A64D0A83B3A4508B2D`
- Executable SHA256: `089F72636B6D5038797BB0086871CABE66C06189322155DEBCF81DF816F65C82`

## 📜 Full Changelog

See [CHANGELOG.md](https://github.com/melerek/PostMini/blob/main/CHANGELOG.md) for complete version history.
