# Variable Status Highlighting Feature

**PostMini v1.7.2** | Smart Variable Validation

---

## 📋 Overview

PostMini now provides **intelligent variable highlighting** that changes color based on whether variables are defined or undefined. This makes it easy to spot missing variables before sending requests.

---

## 🎨 Color Coding

### Dark Theme
- **🟢 Green (`#4CAF50`)**: Variable is defined and has a value
- **🔴 Red (`#F44336`)**: Variable is undefined or missing

### Light Theme
- **🟢 Dark Green (`#2E7D32`)**: Variable is defined and has a value
- **🔴 Dark Red (`#D32F2F`)**: Variable is undefined or missing

---

## ✨ Features

### 1. **URL Field Highlighting**

Variables in the URL field are highlighted based on their status:

```
Example: {{baseUrl}}/users/{{userId}}

✅ If both variables are defined:
   🟢 {{baseUrl}} 🟢 /users/ 🟢 {{userId}}

❌ If userId is missing:
   🟢 {{baseUrl}} /users/ 🔴 {{userId}}
```

### 2. **Table Cell Highlighting (Params & Headers)**

Variables in Params and Headers tables show colored highlighting:

| Key | Value |
|-----|-------|
| Authorization | Bearer 🟢 {{authToken}} |
| User-ID | 🔴 {{missingVar}} |

### 3. **Real-Time Validation**

Highlighting updates automatically when:
- You switch environments
- You add/remove variables
- You extract variables from responses
- You type new variable names

### 4. **Comprehensive Variable Sources**

The system checks variables from all sources:
- **Environment Variables** - From selected environment
- **Collection Variables** - From current collection
- **Extracted Variables** - From response extraction
- **Dynamic Variables** - Auto-generated (`$guid`, `$timestamp`, etc.)

---

## 💡 Usage Examples

### Example 1: Spotting Undefined Variables

**Before Sending Request:**
```
URL: {{baseUrl}}/api/{{version}}/users

🟢 {{baseUrl}} → https://api.example.com
🔴 {{version}} → ❌ Undefined
```

**Action Required:**
1. Notice the red highlighting on `{{version}}`
2. Add `version` variable to your environment
3. Variable turns green ✅
4. Now safe to send request

### Example 2: Environment Switching

**With "Development" environment:**
```
Headers:
  API-Key: 🟢 {{devApiKey}}
```

**Switch to "Production" environment:**
```
Headers:
  API-Key: 🔴 {{devApiKey}}  ← Variable doesn't exist in Production!
```

**Solution:** Use common variable names across environments, or add the variable to Production environment.

### Example 3: Variable Extraction Workflow

**Step 1: Login Request**
```
POST {{baseUrl}}/auth/login

Response:
{
  "token": "abc123xyz..."
}
```

**Step 2: Before Extraction**
```
GET {{baseUrl}}/protected/data
Headers:
  Authorization: Bearer 🔴 {{extracted.authToken}}  ← Not extracted yet!
```

**Step 3: After Extraction**
```
(Click "token" value in Extract Variables tab → Save as "authToken")

GET {{baseUrl}}/protected/data
Headers:
  Authorization: Bearer 🟢 {{extracted.authToken}}  ← Now defined! ✅
```

---

## 🔍 How It Works

### Variable Resolution Process

1. **Parse Text**: Find all `{{variableName}}` patterns
2. **Check Definition**: Query environment manager for variable value
3. **Determine Color**:
   - If variable exists with non-empty value → 🟢 Green
   - If variable doesn't exist or is empty → 🔴 Red
4. **Apply Highlighting**: Draw colored background behind variable

### Checked Sources (in order)

```
Priority 1: Extracted Variables ({{extracted.variableName}})
Priority 2: Environment Variables (from selected environment)
Priority 3: Collection Variables (from current collection)
Priority 4: Dynamic Variables ($variableName)
```

### Definition Criteria

A variable is considered **defined** if:
- ✅ Variable name exists in any source
- ✅ Value is not `None`
- ✅ Value is not empty string `""`
- ✅ Value is not `"❌ Undefined"`

---

## 🎯 Best Practices

### 1. **Check Red Variables Before Sending**

Always review your request for red-highlighted variables:
- They indicate missing configuration
- Requests will likely fail with these undefined
- Fix them before sending to avoid errors

### 2. **Use Consistent Variable Names**

```
❌ Bad: Different names per environment
  Dev: {{devApiKey}}
  Prod: {{prodApiKey}}

✅ Good: Same name, different values
  Dev: {{apiKey}} = "dev-key-123"
  Prod: {{apiKey}} = "prod-key-xyz"
```

### 3. **Document Required Variables**

In collection descriptions, list all required variables:
```
Required Environment Variables:
- baseUrl: API base URL
- apiKey: Your API key
- userId: Current user ID

All should be 🟢 green before running requests
```

### 4. **Use Variable Inspector**

Click **"📊 Variables"** in toolbar to see all available variables and verify none are missing.

---

## 🐛 Troubleshooting

### Variable Shows Red But Should Be Defined

**Possible Causes:**

1. **Environment Not Selected**
   - Solution: Select environment from dropdown in toolbar

2. **Variable Name Mismatch**
   ```
   Environment: baseURL (uppercase L)
   Request: {{baseUrl}} (lowercase l)
   
   Solution: Fix spelling to match exactly
   ```

3. **Variable Value Is Empty**
   ```
   Environment: apiKey = ""
   
   Solution: Set a non-empty value
   ```

4. **Wrong Environment Selected**
   ```
   Current: Production
   Variable: {{devApiKey}} (only in Development)
   
   Solution: Switch to Development environment
   ```

### Variable Shows Green But Doesn't Work

**Possible Causes:**

1. **Stale Cache**
   - Solution: Switch to another tab and back, or restart app

2. **Variable Not Updated After Change**
   - Solution: Click away from field and back to trigger update

---

## 🔧 Technical Details

### Implementation

**Classes Modified:**
- `HighlightedLineEdit` - URL field highlighting
- `VariableHighlightDelegate` - Table cell highlighting

**New Methods:**
- `_is_variable_defined(var_name)` - Checks if variable exists in environment manager

**Color Constants:**
```python
# Dark Theme
var_defined_color = QColor("#4CAF50")     # Green
var_undefined_color = QColor("#F44336")   # Red

# Light Theme  
var_defined_color = QColor("#2E7D32")     # Dark Green
var_undefined_color = QColor("#D32F2F")   # Dark Red
```

### Performance

- **Real-time checking**: Variables are validated during paint events
- **Minimal overhead**: Lookups are cached by environment manager
- **No network calls**: All checking is done locally

---

## 📊 Comparison with v1.7.1

| Feature | v1.7.1 | v1.7.2 (New) |
|---------|--------|--------------|
| **Variable Highlighting** | Purple (all variables) | Green/Red (based on status) |
| **Undefined Detection** | Only in tooltips | Visual color coding |
| **Error Prevention** | Manual check | Instant visual feedback |
| **Workflow** | Check → Send → Debug | Check → Fix → Send |

---

## ✅ Benefits

### For Developers
- **Faster debugging**: Spot issues before sending
- **Better confidence**: Know all variables are defined
- **Less trial-and-error**: Fix problems proactively

### For QA Engineers
- **Test validation**: Ensure test data is properly configured
- **Environment verification**: Quickly check correct environment is active
- **Documentation**: Easily identify required vs optional variables

### For Teams
- **Onboarding**: New team members can see which variables are needed
- **Standards**: Encourages consistent variable naming
- **Quality**: Reduces failed requests due to missing variables

---

## 🎓 Visual Guide

### Status Indicators

```
🟢 GREEN = Good to go!
   ✅ Variable is defined
   ✅ Has a value
   ✅ Ready to use

🔴 RED = Action needed!
   ❌ Variable is undefined
   ❌ No value set
   ❌ Will cause errors
```

### Quick Check Workflow

```
1. Type your request with variables
2. Look for red highlighting
3. If any red:
   - Add missing variables
   - Select correct environment
   - Extract from previous responses
4. When all green:
   - Click Send ✅
```

---

## 📚 Related Features

- **[Variable Highlighting Guide](VARIABLE_HIGHLIGHTING_GUIDE.md)** - Complete variable highlighting documentation
- **[Environment Variables Guide](ENVIRONMENT_VARIABLES_GUIDE.md)** - Managing environments
- **[QA Features Guide](QA_FEATURES_GUIDE.md)** - Variable extraction

---

## 🎉 Summary

Variable status highlighting provides instant visual feedback about variable definition status:

- **🟢 Green**: Variable is defined and ready to use
- **🔴 Red**: Variable is undefined and needs attention

This feature helps prevent errors and speeds up API testing workflows!

---

**Happy API Testing! 🚀**

*PostMini v1.7.2 - Smart Variable Validation*

