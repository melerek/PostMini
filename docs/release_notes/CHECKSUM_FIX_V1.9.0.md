# Auto-Update Checksum Fix - v1.9.0

## Issue
Auto-update feature failed with error:
```
Failed to download update:
Checksum verification failed. Downloaded file may be corrupted.
Please try again later or download manually from the website.
```

## Root Cause
The `version.json` file contained a placeholder checksum value (`"checksum": "sha256:TBD"`) instead of the actual SHA256 hash of the installer file.

## Solution
Calculated and updated the actual SHA256 checksum for `PostMini_Setup_v1.9.0.exe`

### Checksum Details
**File:** `PostMini_Setup_v1.9.0.exe`  
**SHA256:** `507AE526568FBB7C211E660C697DF1DCC36AEF8A564B0D8E4D13080AF46A37F6`

## Files Updated

### 1. version.json
**Before:**
```json
"checksum": "sha256:TBD"
```

**After:**
```json
"checksum": "sha256:507AE526568FBB7C211E660C697DF1DCC36AEF8A564B0D8E4D13080AF46A37F6"
```

### 2. RELEASE_V1.9.0_INSTRUCTIONS.md
Updated the checksums section to include the actual hash for user verification.

## How It Works
1. PostMini downloads the installer from GitHub releases
2. Calculates SHA256 hash of downloaded file
3. Compares with checksum in `version.json` (from GitHub repo)
4. If they match → Install proceeds
5. If they don't match → Shows error (prevents corrupted/tampered files)

## Testing Auto-Update
After publishing the release to GitHub:

1. Make sure `version.json` is committed and pushed to GitHub
2. Open an older version of PostMini (v1.8.6 or earlier)
3. PostMini will check for updates
4. Click "Update Now" when prompted
5. Download and verification should succeed
6. Installer will launch automatically

## Important Notes

⚠️ **CRITICAL:** You must push the updated `version.json` to GitHub BEFORE or AT THE SAME TIME as publishing the release. Otherwise users will still get the "TBD" checksum.

✅ **Recommended Workflow:**
1. Commit and push `version.json` with correct checksum
2. Create GitHub release and upload installer
3. Users can now auto-update successfully

## Verification Command
Users (or you) can verify the installer integrity manually:

```powershell
Get-FileHash PostMini_Setup_v1.9.0.exe -Algorithm SHA256
```

Expected output:
```
Algorithm       Hash
---------       ----
SHA256          507AE526568FBB7C211E660C697DF1DCC36AEF8A564B0D8E4D13080AF46A37F6
```

---

**Status:** ✅ FIXED  
**Date:** November 13, 2025  
**Impact:** Auto-update feature will now work correctly for v1.9.0
