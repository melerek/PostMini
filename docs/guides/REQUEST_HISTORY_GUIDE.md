# Request History - User Guide

## Overview

The Request History feature automatically tracks all your API requests, allowing you to:
- 📊 **Review** all executed requests with responses
- 🔍 **Debug** issues by examining past requests
- 🔄 **Replay** successful requests instantly
- 📈 **Analyze** performance trends
- 🐛 **Track** failed requests

## Features

✅ **Automatic Tracking** - Every request is automatically saved  
✅ **Complete Context** - Request details, response data, timing  
✅ **Filtering** - By status, collection, success/failure  
✅ **Replay** - Load and re-execute any past request  
✅ **Performance Metrics** - Response time and size tracking  
✅ **Error Tracking** - All errors saved for debugging  

---

## How to Access History

### Method 1: Toolbar Button
1. Look for the **"📋 History"** button in the top toolbar
2. Click it to open the History dialog

### Quick Tip:
The History button is right next to "Manage Environments" in the toolbar.

---

## Understanding the History Dialog

### Main Table Columns:

| Column | Description |
|--------|-------------|
| **Time** | When the request was sent (YYYY-MM-DD HH:MM:SS) |
| **Method** | HTTP method (GET, POST, etc.) |
| **URL** | Request URL (truncated if too long) |
| **Status** | HTTP status code (color-coded) |
| **Time (s)** | Response time in seconds |
| **Size** | Response size (B, KB, or MB) |
| **Collection** | Request name if from saved collection |

### Status Color Coding:
- 🟢 **Green (2xx)** - Successful
- 🔵 **Blue (3xx)** - Redirect
- 🟠 **Orange (4xx)** - Client Error
- 🔴 **Red (5xx)** - Server Error
- 🔴 **Red (Error)** - Network/Connection Error

---

## Using Filters

The History dialog includes powerful filtering:

### Available Filters:

**1. All Requests**
   - Shows everything
   - Default view

**2. Successful (2xx)**
   - Only requests with 200-299 status codes
   - Use for: Finding working requests

**3. Client Errors (4xx)**
   - Status codes 400-499
   - Use for: Finding bad requests, auth issues

**4. Server Errors (5xx)**
   - Status codes 500-599
   - Use for: Finding server problems

**5. Failed Requests**
   - Any 4xx, 5xx, or connection errors
   - Use for: Debugging problems

### How to Filter:
1. Use the **"Filter:"** dropdown at the top
2. Select your desired filter
3. Table updates immediately

---

## Viewing Request Details

### To See Full Details:
1. **Click on any row** in the history table
2. Details appear in the bottom panel
3. Two tabs available:
   - **Request** tab - Request details
   - **Response** tab - Response details

### Request Tab Shows:
- Method and URL
- Query parameters (if any)
- Headers (if any)
- Request body (if any)
- Authentication type

### Response Tab Shows:
- Status code
- Response time
- Response size
- Response headers
- Response body
- Error message (if failed)

---

## Replaying Requests

### Method 1: Double-Click
1. **Double-click** any row in the history table
2. Request loads into main window
3. Click "Send" to execute

### Method 2: Replay Button
1. **Single-click** a row to select it
2. Click **"Replay Request"** button at bottom
3. Request loads into main window
4. Click "Send" to execute

### What Gets Loaded:
✅ HTTP Method  
✅ URL  
✅ Query parameters  
✅ Headers  
✅ Request body  
✅ Authentication settings  

### Note:
- Replaying **loads** the request but doesn't execute it
- You can modify before sending
- Original request is not affected

---

## Managing History

### Refreshing the View:
- Click **"Refresh"** button to reload latest data
- Useful if you send requests while dialog is open

### Clearing History:
1. Click **"Clear History"** button
2. Confirmation dialog appears
3. Click **"Yes"** to confirm
4. All history is permanently deleted

⚠️ **Warning:** Clearing history cannot be undone!

---

## Use Cases

### 1. Debugging Failed Requests

**Scenario:** API call failed, need to investigate

**Steps:**
1. Open History
2. Filter: **"Failed Requests"**
3. Find the failed request
4. Click to view details
5. Check error message in Response tab
6. Fix issue and replay

**Example:**
```
Status: 401
Error: Unauthorized - Invalid API token

Solution: Update API token in headers and replay
```

### 2. Performance Analysis

**Scenario:** Check if API is getting slower

**Steps:**
1. Open History
2. Filter: **"All Requests"**
3. Look at **Time (s)** column
4. Compare recent vs older requests
5. Identify slow endpoints

**Example:**
```
Same endpoint:
Yesterday: 0.234s
Today: 1.523s
→ Performance degradation detected!
```

### 3. Reproducing Issues

**Scenario:** User reports error, can't reproduce

**Steps:**
1. Open History
2. Find the exact request from that time
3. View full request details
4. Replay with same parameters
5. See the actual error

**Example:**
```
User: "Create user failed"
History shows:
  POST /users
  Body: {"name": "John@Doe"}
  Status: 400
  Error: Invalid email format
→ Issue found and fixed!
```

### 4. Testing Different Scenarios

**Scenario:** Test same endpoint with different params

**Steps:**
1. Send request with params A
2. Send request with params B
3. Send request with params C
4. Open History
5. Compare all three responses
6. Choose best approach

### 5. Sharing with Team

**Scenario:** Show teammate exact request that worked

**Steps:**
1. Open History
2. Find successful request
3. Take screenshot or:
4. Replay → Save as new request
5. Export collection
6. Share with team

---

## Advanced Tips

### Tip 1: Quick Success Check
```
Filter: Successful (2xx)
Look for: Your latest test
If found: Request working!
If not found: Check Failed Requests filter
```

### Tip 2: Performance Baseline
```
Before changes:
  - Record average response time
  
After changes:
  - Compare with history
  - Identify regressions
```

### Tip 3: Error Pattern Detection
```
Filter: Failed Requests
Sort by: Time
Pattern: Multiple 500 errors in row
→ Server might be down!
```

### Tip 4: API Behavior Analysis
```
Same request at different times:
  10:00 AM - Status 200, 0.2s
  12:00 PM - Status 200, 0.5s
  02:00 PM - Status 503, Error
→ Server overload during peak hours
```

---

## Limitations & Notes

### Storage:
- ✅ Unlimited history entries
- ✅ Large responses truncated to 100KB
- ⚠️ Very large history may slow down queries
- 💡 Use "Clear History" periodically

### What's NOT Saved:
- ❌ Actual response images/files
- ❌ Streaming responses
- ❌ WebSocket connections
- ✅ Everything else is saved!

### Privacy:
- ⚠️ Sensitive data (tokens, passwords) IS saved
- ⚠️ History stored in local database
- 💡 Clear history before sharing database
- 💡 Use environment variables for secrets

---

## Troubleshooting

### Issue: History dialog empty

**Possible Causes:**
1. No requests sent yet
2. History was cleared
3. Filter too restrictive

**Solutions:**
- Send a request first
- Change filter to "All Requests"
- Check total count in top-right

### Issue: Can't replay request

**Possible Causes:**
1. No row selected
2. Corrupted history entry

**Solutions:**
- Click a row first
- Check Request tab for data
- Try different entry

### Issue: Missing response body

**Possible Causes:**
1. Response was empty
2. Response was too large (truncated)
3. Error occurred before response

**Solutions:**
- Check Response tab for details
- Look for "(truncated)" text
- Check error_message field

### Issue: Slow history loading

**Possible Causes:**
1. Too many history entries (10,000+)
2. Large database file

**Solutions:**
- Clear old history
- Use filters to reduce results
- Consider periodic cleanup

---

## Keyboard Shortcuts (Future)

Coming soon:
- `Ctrl+H` - Open History
- `Enter` - Replay selected
- `Delete` - Clear history
- `F5` - Refresh

---

## FAQ

**Q: How long is history kept?**  
A: Forever, until you manually clear it.

**Q: Can I export history?**  
A: Not directly, but you can export the database file.

**Q: Does history slow down the app?**  
A: Not noticeably, even with thousands of entries.

**Q: Are variables substituted in history?**  
A: Yes! History saves the actual URL after substitution.

**Q: Can I search history?**  
A: Not yet, but filters help narrow down results.

**Q: Does clearing history affect collections?**  
A: No! Collections and requests are separate.

**Q: Can I see history for deleted collections?**  
A: Yes! History persists even if collection is deleted.

**Q: What happens on app restart?**  
A: History persists in database, available immediately.

---

## Best Practices

### ✅ DO:

1. **Regular Review**
   - Check failed requests daily
   - Analyze performance trends weekly

2. **Periodic Cleanup**
   - Clear very old history (6+ months)
   - Especially before sharing database

3. **Use Filters**
   - Don't scroll through everything
   - Use filters to find what you need

4. **Replay for Testing**
   - Instead of retyping requests
   - Faster and more accurate

5. **Debug with History**
   - First place to check for issues
   - Better than relying on memory

### ❌ DON'T:

1. **Don't** rely solely on history for backups
   - Use collection export for that

2. **Don't** ignore failed requests
   - They indicate real problems

3. **Don't** let history grow forever
   - Clean up periodically

4. **Don't** share database with sensitive history
   - Clear first or use environment variables

---

## Integration with Other Features

### Works With:

**Environment Variables**
- History saves URLs AFTER variable substitution
- Shows actual endpoints used
- Helps verify variable values

**Collections**
- History tracks which collection request came from
- Filter by collection available
- Doesn't affect saved collection requests

**Export/Import**
- History NOT included in collection exports
- History is local only
- Intentional for privacy

---

## Real-World Example

### Debugging Production Issue:

**Initial Report:**
```
User: "Can't create account"
Time: 2:30 PM
```

**Investigation:**
```
1. Open History
2. Filter: Failed Requests
3. Find 2:30 PM entries
4. See: POST /register
5. Status: 400
6. Response: "Email already exists"
```

**Resolution:**
```
1. Replay request
2. Modify email
3. Send successfully
4. Identify duplicate check issue
5. Fix validation message
6. Test with replay
```

**Time Saved:** 15 minutes of guesswork!

---

## Statistics

Your history helps you understand:
- Total requests sent
- Success rate
- Average response time
- Most used endpoints
- Error patterns

Check the **stats** in top-right of History dialog!

---

## Support

Having issues?
1. Check this guide
2. Review troubleshooting section
3. Clear and refresh history
4. Check main README.md

---

**Happy Debugging with Request History! 🚀**

