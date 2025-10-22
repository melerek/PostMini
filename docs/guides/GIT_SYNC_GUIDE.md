# Git Sync Guide

**Git-Based Collaboration for PostMini**

Git Sync enables seamless team collaboration by version-controlling your API collections, environments, and tests alongside your codebase. No cloud infrastructure required—just Git!

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Getting Started](#getting-started)
3. [User Workflows](#user-workflows)
4. [Best Practices](#best-practices)
5. [Secrets Management](#secrets-management)
6. [Troubleshooting](#troubleshooting)
7. [FAQ](#faq)

---

## Overview

### What is Git Sync?

Git Sync automatically saves your PostMini collections, environments, and tests as JSON files in a `.postmini/` folder within your project directory. These files can be committed to Git, enabling your team to:

- ✅ Share API collections as code
- ✅ Review changes via Pull Requests
- ✅ Track history and roll back changes
- ✅ Keep APIs in sync with code changes
- ✅ Work offline and sync later

### How It Works

```
PostMini Database  ←→  .postmini/ Files  ←→  Git Repository
     (SQLite)          (JSON files)       (Version Control)
                              
     [Save]  →  [Export]  →  [git commit]  →  [git push]
     [Load]  ←  [Import]  ←  [git pull]
```

**⚠️ IMPORTANT:** PostMini does **NOT** run Git commands automatically!

**What PostMini Does:**
- ✅ Syncs between database and `.postmini/` files
- ✅ Auto-exports on save (if enabled)
- ✅ Detects file changes for import

**What YOU Must Do:**
- ❗ Run `git add`, `git commit`, `git push` manually
- ❗ Run `git pull` before importing
- ❗ Resolve Git conflicts if they occur

```
my-project/
├── src/                    # Your application code
├── .postmini/             # YOU commit this to Git
│   ├── collections/
│   │   ├── user-api.json
│   │   └── payment-api.json
│   ├── environments/
│   │   ├── development.json
│   │   └── production.json
│   └── workspace.json
├── .postmini-secrets/     # Gitignored (local only)
│   └── local-secrets.json
└── .gitignore
```

**Key Points:**
- `.postmini/` is committed to Git (shareable) - **BY YOU**
- `.postmini-secrets/` is gitignored (local secrets only)
- Secrets are automatically separated from shareable configs
- PostMini = File Sync, Git = Version Control (separate steps!)

---

## Getting Started

### Step 1: Enable Git Sync

1. Open PostMini
2. Click **🔄 Git Sync** in the toolbar
3. Go to the **Setup** tab
4. Click **Browse** and select your project directory
5. Check ✅ **Enable auto-sync** (recommended)
6. Check ✅ **Add .postmini-secrets/ to .gitignore** (recommended)
7. Click **🚀 Enable Git Sync**

### Step 2: Initial Sync

PostMini will:
- Create `.postmini/` folder structure
- Export your current collections and environments
- Add `.postmini-secrets/` to `.gitignore`

### Step 3: Commit to Git

```bash
git add .postmini/
git add .gitignore
git commit -m "Add API collections"
git push origin main
```

✅ **Done!** Your collections are now in version control.

---

## User Workflows

### Scenario 1: Starting a New Project

**John (Backend Engineer) sets up the project:**

```bash
# 1. Clone/create project
git clone https://github.com/company/my-project.git
cd my-project

# 2. Open PostMini and enable Git Sync
# PostMini GUI: 🔄 Git Sync → Setup → Enable

# 3. Create collections and requests
# ... use PostMini normally ...

# 4. Collections are auto-synced to .postmini/
# 5. Commit to Git
git add .postmini/
git commit -m "Add initial API collections"
git push
```

---

### Scenario 2: Teammate Joins Project

**Sarah (Frontend Engineer) clones and imports:**

```bash
# 1. Clone the repository
git clone https://github.com/company/my-project.git
cd my-project

# 2. Open PostMini
# PostMini automatically detects .postmini/ folder!

# 3. PostMini shows dialog:
┌─────────────────────────────────────────────┐
│  Import Project Collections?                │
├─────────────────────────────────────────────┤
│  Found collections in:                      │
│  C:\projects\my-project\.postmini\          │
│                                             │
│  Collections to import:                     │
│  ☑ User API (12 requests)                   │
│  ☑ Payment API (8 requests)                 │
│                                             │
│  [ Skip ]  [ Import to New Workspace ]      │
└─────────────────────────────────────────────┘

# 4. Click "Import to New Workspace"
# ✅ Done! Sarah has all of John's collections
```

---

### Scenario 3: Making Changes & Sharing

**Sarah adds a new request:**

1. **In PostMini:**
   - Add new request "Get User Profile"
   - Click **Save** (auto-syncs to `.postmini/`)

2. **In terminal:**
   ```bash
   git status
   # Modified: .postmini/collections/user-api.json
   
   git diff .postmini/collections/user-api.json
   # Shows the new request in JSON format
   
   git checkout -b feature/user-profile-endpoint
   git add .postmini/
   git commit -m "Add Get User Profile endpoint"
   git push origin feature/user-profile-endpoint
   ```

3. **Create Pull Request:**
   - Teammates can review the API changes in the PR
   - Just like code review!

4. **After merge, teammates pull:**
   ```bash
   git pull origin main
   ```
   
   PostMini shows:
   ```
   ⚠️ Collections Updated
   Git sync detected changes:
   
   ↻ User API - 1 request added
   
   [ View Changes ]  [ Sync Now ]
   ```
   
   Click **Sync Now** → changes imported!

---

### Scenario 4: Handling Conflicts

**Both John and Sarah modified the same collection:**

```bash
# Sarah tries to pull:
git pull origin main

CONFLICT (content): Merge conflict in .postmini/collections/user-api.json
```

**PostMini helps resolve:**

1. PostMini detects conflict and shows dialog:
   ```
   🔧 Merge Conflict Detected
   
   Collection: User API
   Conflicting requests: "Create User" (both modified)
   
   Choose version:
   ○ Keep yours (local)
   ○ Use theirs (remote)
   ● Merge both (manual)
   ```

2. **Option 1: Keep Yours**
   - Overwrites remote with your version
   - Use if you're sure your changes are correct

3. **Option 2: Use Theirs**
   - Discards your changes, uses remote version
   - Use if their changes should take precedence

4. **Option 3: Manual Merge (Recommended)**
   - PostMini opens side-by-side comparison
   - You select which parts to keep
   - Best for complex conflicts

---

## Best Practices

### ✅ DO:

1. **Commit `.postmini/` to Git**
   ```bash
   git add .postmini/
   git commit -m "Update API collections"
   ```

2. **Use Branches for New Features**
   ```bash
   git checkout -b feature/new-api-endpoint
   # ... make changes in PostMini ...
   git add .postmini/
   git commit -m "Add new endpoint"
   ```

3. **Pull Before Push**
   ```bash
   git pull origin main
   # PostMini will prompt to import changes
   git push origin main
   ```

4. **Review Collections in PRs**
   - Check the JSON diffs in `.postmini/`
   - Verify new requests make sense
   - Approve like any code change

5. **Keep Auto-Sync Enabled**
   - Saves automatically when you click "Save"
   - Less chance of forgetting to sync

### ❌ DON'T:

1. **Don't Commit `.postmini-secrets/`**
   - Contains your local API keys
   - Already gitignored by default
   - Never remove from `.gitignore`!

2. **Don't Edit `.postmini/*.json` Files Directly**
   - Use PostMini GUI instead
   - Manual edits might break sync
   - Exception: Resolving Git conflicts

3. **Don't Force Push Collections**
   ```bash
   # ❌ BAD - Never force push
   git push --force origin main
   
   # ✅ GOOD - Resolve conflicts properly
   git pull origin main
   # Use PostMini conflict resolution
   git push origin main
   ```

4. **Don't Share Secrets in Collections**
   - Use `{{variableName}}` placeholders
   - Each team member sets their own secrets locally
   - See [Secrets Management](#secrets-management)

---

## Secrets Management

### How Secrets Work

**Shared Config (in Git):**
```json
{
  "name": "Production",
  "variables": {
    "baseUrl": "https://api.example.com",
    "apiKey": "{{SECRET_PRODUCTION_APIKEY}}",
    "timeout": "5000"
  }
}
```

**Local Secrets (NOT in Git):**
```json
{
  "production": {
    "SECRET_PRODUCTION_APIKEY": "your-actual-secret-key-here"
  }
}
```

### Setting Up Secrets

**When you import a workspace with secrets:**

1. PostMini shows:
   ```
   🔐 Missing Secrets
   
   The following secrets are not set:
   
   Production:
   • SECRET_PRODUCTION_APIKEY
   
   [ Set Up Secrets ]  [ Skip ]
   ```

2. Click **Set Up Secrets**
3. Enter your secret values
4. Secrets saved to `.postmini-secrets/` (local only)

### Secret Detection

PostMini automatically treats variables as secrets if their name contains:
- `secret`
- `key`
- `token`
- `password`
- `auth`
- `credential`

**Examples:**
- `apiKey` → Secret ✅
- `authToken` → Secret ✅
- `baseUrl` → Not secret ❌
- `timeout` → Not secret ❌

### Team Workflow with Secrets

1. **Engineer 1 creates environment:**
   - Adds `apiKey` variable
   - PostMini auto-separates it as secret
   - Commits public config with placeholder

2. **Engineer 2 pulls the project:**
   - Gets public config with `{{SECRET_DEV_APIKEY}}`
   - PostMini prompts for secret value
   - Engineer 2 enters their own API key
   - Secret saved locally only

3. **Result:**
   - Both engineers use same environment structure
   - Each has their own API keys
   - No secrets leaked in Git ✅

---

## Troubleshooting

### Issue: "Git sync not detecting changes"

**Solution:**
1. Click **🔄 Git Sync** → **Status** tab
2. Click **🔄 Refresh Status**
3. Check "Detected Changes" section
4. Manually click **⬆️ Push** or **⬇️ Pull**

---

### Issue: "Imported collections are empty"

**Possible Causes:**
1. JSON files are malformed
2. Files created by different PostMini version

**Solution:**
1. Check `.postmini/collections/*.json` files
2. Verify JSON is valid (use JSON validator)
3. Try re-exporting from original PostMini instance

---

### Issue: "Secrets not working after import"

**Solution:**
1. Open **🔄 Git Sync** → **Status** tab
2. PostMini will show "🔐 Missing Secrets" dialog
3. Click **Set Up Secrets**
4. Enter your secret values

**Alternative:**
- Manually edit `.postmini-secrets/local-secrets.json`
- Format:
  ```json
  {
    "environment_name": {
      "SECRET_KEY_NAME": "your-value"
    }
  }
  ```

---

### Issue: "Merge conflicts in .postmini/"

**Solution 1: Use PostMini's Conflict Helper**
1. PostMini will detect conflict on startup
2. Shows conflict resolution dialog
3. Choose your resolution strategy

**Solution 2: Manual Resolution**
```bash
# Accept theirs
git checkout --theirs .postmini/collections/user-api.json

# Or accept yours
git checkout --ours .postmini/collections/user-api.json

# Then mark as resolved
git add .postmini/
git commit
```

**Solution 3: Fresh Import**
```bash
# Accept theirs
git checkout --theirs .postmini/

# Re-import in PostMini
# 🔄 Git Sync → Status → ⬇️ Pull from Files
```

---

## FAQ

### Q: Do I need Git installed?

**A:** No! Git Sync just uses the file system. But you need Git to share with teammates.

PostMini works with:
- ✅ Git (most common)
- ✅ Any file sync (Dropbox, OneDrive, etc.)
- ✅ Manual file sharing
- ✅ Local projects (solo work)

---

### Q: Can I use Git Sync for multiple projects?

**A:** Yes! Enable Git Sync separately for each project directory. PostMini tracks all active workspaces.

View all workspaces: **🔄 Git Sync** → **Workspaces** tab

---

### Q: What happens if I disable Git Sync?

**A:** 
- Auto-sync stops
- `.postmini/` files remain (not deleted)
- You can re-enable anytime
- No data is lost

---

### Q: Can I edit .postmini files manually?

**A:** Yes, but not recommended. The JSON format is straightforward, but manual edits might cause sync issues. Use PostMini GUI for safety.

**Safe to edit:**
- `.gitignore` (to customize)
- `.postmini/workspace.json` (metadata only)

**Not recommended:**
- Collection JSON files
- Environment JSON files

---

### Q: How do I switch between Git branches?

**A:** PostMini detects branch changes automatically!

```bash
# Switch to feature branch
git checkout feature/new-api

# PostMini shows:
"Collections updated to match branch 'feature/new-api'"

# Switch back to main
git checkout main

# Collections automatically revert
```

---

### Q: Does Git Sync work offline?

**A:** Yes! Git Sync works entirely offline. Just sync to filesystem, commit when ready, and push when online.

---

### Q: Can I use Postman collections?

**A:** Yes! PostMini supports importing Postman Collection Format v2.1:

1. Export from Postman as JSON
2. In PostMini: **File** → **Import Collection**
3. Select Postman JSON file
4. PostMini auto-converts to PostMini format
5. Enable Git Sync to version control it

---

### Q: What about large binary responses?

**A:** Request history stores responses up to 100KB. Git Sync only stores request definitions (not responses), so binary data isn't a concern.

---

### Q: How do I collaborate with non-developers?

**A:** 
1. **Git-savvy users:** Use Git normally
2. **Non-Git users:** 
   - Export collections as ZIP
   - Share via email/Slack
   - They import using PostMini

Git Sync is optional—you can always use manual import/export.

---

## Status Indicators

PostMini shows sync status in the toolbar:

| Indicator | Meaning | Action |
|-----------|---------|--------|
| `Git: Not Enabled` | Git sync is off | Enable in settings |
| `Git: ✅ Synced` | All changes synced | Nothing needed |
| `Git: ⬆️ Push Needed` | Database has unsaved changes | Push to filesystem |
| `Git: ⬇️ Pull Available` | Filesystem has new changes | Pull from filesystem |
| `Git: ⚠️ Conflict` | Both have changes | Resolve conflict |

---

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+S` | Save request (auto-syncs if enabled) |
| `Ctrl+Shift+G` | Open Git Sync dialog |

---

## Summary

**Git Sync enables powerful team collaboration:**

✅ Collections live alongside code  
✅ PR reviews for API changes  
✅ Version control and history  
✅ Branch-based workflows  
✅ Secrets kept local and safe  
✅ No cloud infrastructure needed  

**Get started in 3 steps:**
1. Enable Git Sync in PostMini
2. Commit `.postmini/` to Git
3. Share with your team!

---

**Need Help?**
- Check [Troubleshooting](#troubleshooting)
- See [Best Practices](#best-practices)
- Open an issue on GitHub

**Happy Collaborating! 🚀**

