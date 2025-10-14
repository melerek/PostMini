# cURL Import/Export Guide

**Feature:** Import cURL commands and export requests as cURL  
**Added:** Version 1.1.0  
**Status:** ✅ Fully Implemented

---

## 📋 Overview

PostMini now supports importing cURL commands directly from your clipboard and exporting requests as cURL commands. This makes it easy to:

- Copy cURL from API documentation and import it instantly
- Share requests with teammates via command line
- Use PostMini requests in terminal/scripts
- Test APIs quickly without manual configuration

---

## 📥 Importing cURL Commands

###Step 1: Copy a cURL Command

From API documentation, browser DevTools, or anywhere else:

```bash
curl -X POST 'https://api.github.com/user/repos' \
  -H 'Accept: application/vnd.github.v3+json' \
  -H 'Authorization: token YOUR_TOKEN' \
  -H 'Content-Type: application/json' \
  -d '{
    "name": "Hello-World",
    "description": "This is your first repo"
  }'
```

### Step 2: Select a Collection

1. Open PostMini
2. **Select a collection** in the left panel (or create a new one)
3. The cURL command will be imported into this collection

### Step 3: Click "Import cURL"

1. Click the **"📋 Import cURL"** button in the collections panel
2. A dialog will open

### Step 4: Paste and Preview

1. **Paste** your cURL command into the text area
2. Click **"🔍 Preview"** to see what will be imported:
   - Method (GET, POST, etc.)
   - URL
   - Headers
   - Query parameters
   - Request body

### Step 5: Import

1. If the preview looks good, click **"📥 Import"**
2. Enter a name for the request (auto-suggested based on URL)
3. Click **OK**

**Result:** ✅ The request is created with all settings from the cURL command!

---

## 📤 Exporting as cURL

### Option 1: Via Code Generation Dialog

1. Open/select a request in PostMini
2. Click the **"💻 Code"** button
3. Select **"cURL"** from the language dropdown
4. Copy the generated command

### Option 2: Quick Copy (Future Enhancement)

*Coming soon:* Right-click on a request → "Copy as cURL"

---

## 🎯 Supported cURL Flags

PostMini supports the most commonly used cURL flags:

| Flag | Long Form | Description | Supported |
|------|-----------|-------------|-----------|
| `-X` | `--request` | HTTP method | ✅ |
| `-H` | `--header` | Custom header | ✅ |
| `-d` | `--data` | Request body | ✅ |
|  | `--data-raw` | Raw request body | ✅ |
|  | `--data-binary` | Binary data | ✅ |
|  | `--json` | JSON data (sets Content-Type) | ✅ |
| `-A` | `--user-agent` | User agent | ✅ |
| `-e` | `--referer` | Referer header | ✅ |
| `-u` | `--user` | Basic auth | ✅ |
|  | `--compressed` | Accept-Encoding header | ✅ |
| `-k` | `--insecure` | Skip SSL verification | ⚠️ Ignored |
| `-L` | `--location` | Follow redirects | ⚠️ Ignored |
| `-s` | `--silent` | Silent mode | ⚠️ Ignored |
| `-o` | `--output` | Output file | ⚠️ Ignored |

**Note:** Flags marked as "Ignored" are parsed but don't affect the imported request (they're terminal-specific).

---

## 📝 Examples

### Example 1: Simple GET Request

**cURL:**
```bash
curl 'https://api.example.com/users?page=1&limit=10'
```

**Imports as:**
- Method: `GET`
- URL: `https://api.example.com/users`
- Params: `page=1`, `limit=10`

---

### Example 2: POST with JSON

**cURL:**
```bash
curl -X POST 'https://api.example.com/users' \
  -H 'Content-Type: application/json' \
  -d '{"name": "John Doe", "email": "john@example.com"}'
```

**Imports as:**
- Method: `POST`
- URL: `https://api.example.com/users`
- Headers: `Content-Type: application/json`
- Body: `{"name": "John Doe", "email": "john@example.com"}`

---

### Example 3: With Bearer Token

**cURL:**
```bash
curl 'https://api.example.com/protected' \
  -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIs...'
```

**Imports as:**
- Method: `GET`
- URL: `https://api.example.com/protected`
- Headers: `Authorization: Bearer eyJhbGciOiJIUzI1NiIs...`

---

### Example 4: DELETE Request

**cURL:**
```bash
curl -X DELETE 'https://api.example.com/users/123' \
  -H 'Authorization: Bearer token123'
```

**Imports as:**
- Method: `DELETE`
- URL: `https://api.example.com/users/123`
- Headers: `Authorization: Bearer token123`

---

## 🔄 Round-Trip Compatibility

PostMini maintains round-trip compatibility:

1. **Import cURL** → Request in PostMini
2. **Export as cURL** → Get the command back
3. **Import again** → Same request

This ensures you can seamlessly move between command-line and GUI workflows.

---

## 💡 Use Cases

### 1. API Documentation Workflow

**Scenario:** API docs provide cURL examples

**Solution:**
1. Copy cURL from docs
2. Import to PostMini
3. Save in a collection
4. Reuse and modify as needed

---

### 2. Browser DevTools

**Scenario:** Inspect network request in Chrome/Firefox

**Solution:**
1. Right-click on request in Network tab
2. "Copy as cURL"
3. Import to PostMini
4. Test and debug

---

### 3. Sharing with Teammates

**Scenario:** Share a request with a colleague

**Solution:**
1. Export request as cURL
2. Send command via Slack/email
3. They import it instantly

---

### 4. CI/CD Integration

**Scenario:** Test API in GitHub Actions

**Solution:**
1. Design request in PostMini
2. Export as cURL
3. Use in workflow file

---

## ⚠️ Limitations & Known Issues

### 1. Complex Scripting

**Not Supported:**
- Shell variables (`$VAR`)
- Command substitution (`` `command` ``)
- Piped commands (`curl ... | jq`)

**Workaround:** Replace variables with actual values before importing

---

### 2. File Uploads

**Partial Support:**
- `-d @filename` is parsed as literal string
- `-F` (form data with files) not yet supported

**Workaround:** Manually set up file uploads in PostMini

---

### 3. Client Certificates

**Not Supported:**
- `--cert` and `--key` flags

**Workaround:** Use system certificate store or manual configuration

---

### 4. Cookies

**Limited Support:**
- `-b` cookie flag is parsed as header
- Cookie jar (`-c`) not supported

---

## 🐛 Troubleshooting

### Error: "No URL found in cURL command"

**Cause:** URL is missing or malformed

**Solution:**
- Ensure URL is included: `curl 'https://api.example.com'`
- Check for typos in the URL

---

### Error: "Invalid cURL command"

**Cause:** Syntax error or unsupported shell features

**Solutions:**
- Remove shell variables and replace with values
- Remove piped commands (`| jq`, etc.)
- Ensure quotes are balanced

---

### Preview Shows Wrong Data

**Cause:** Parsing ambiguity

**Solutions:**
- Use quotes around arguments: `-d 'data'` instead of `-d data`
- Use long-form flags: `--header` instead of `-H`
- Remove unnecessary flags (`-s`, `-v`, etc.)

---

### Headers Missing After Import

**Cause:** Headers might be in `-H` or `--header` flags

**Check:**
1. Click Preview before importing
2. Verify headers are shown
3. If missing, add them manually after import

---

## 🚀 Advanced Tips

### Tip 1: Clean Up Generated cURL

When copying from browser DevTools, you might get extra flags:

**From DevTools:**
```bash
curl 'https://api.example.com' \
  -H 'sec-ch-ua: ...' \
  -H 'sec-ch-ua-mobile: ?0' \
  -H 'User-Agent: Mozilla/5.0...' \
  --compressed
```

**Clean version:**
```bash
curl 'https://api.example.com'
```

Remove browser-specific headers before importing.

---

### Tip 2: Use PostMini Variables

After importing, replace hardcoded values with variables:

**Before:**
```
https://api.example.com/users
```

**After:**
```
{{base_url}}/users
```

---

### Tip 3: Combine with Git Sync

1. Import cURL from docs
2. Save to collection
3. Auto-sync to Git
4. Team gets the same requests

---

## 📊 Comparison: cURL vs PostMini UI

| Task | cURL | PostMini |
|------|------|----------|
| **Quick Test** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐☆☆ |
| **Reusability** | ⭐⭐☆☆☆ | ⭐⭐⭐⭐⭐ |
| **Visualization** | ⭐☆☆☆☆ | ⭐⭐⭐⭐⭐ |
| **History** | ⭐☆☆☆☆ | ⭐⭐⭐⭐⭐ |
| **Collaboration** | ⭐⭐⭐⭐☆ | ⭐⭐⭐⭐⭐ |

**Best of both worlds:** Use PostMini for design and management, export as cURL for automation!

---

## 🎓 Learning Resources

### cURL Documentation
- Official docs: https://curl.se/docs/
- Man page: `man curl`
- Tutorial: https://curl.se/docs/tutorial.html

### PostMini Resources
- Main docs: [docs/index.html](index.html)
- Code generation: [CODE_GENERATION_GUIDE.md](CODE_GENERATION_GUIDE.md)
- Collections: [EXPORT_IMPORT_GUIDE.md](EXPORT_IMPORT_GUIDE.md)

---

## 🔮 Future Enhancements

Planned improvements for cURL import/export:

- [ ] Right-click → "Copy as cURL"
- [ ] Import from clipboard with keyboard shortcut
- [ ] Support for `-F` (multipart form data)
- [ ] Import multiple requests from a file
- [ ] cURL import from history/documentation URLs
- [ ] Advanced parsing for shell variables
- [ ] Cookie jar support

---

## 📞 Support

**Having issues?**
- Check [Troubleshooting](#-troubleshooting) section above
- Submit an issue on GitHub
- Check our [FAQ](index.html)

**Feature requests:**
- Open a GitHub issue
- Label it as "enhancement"

---

**Last Updated:** October 2025  
**Version:** 1.1.0  
**Feature Status:** ✅ Production Ready

