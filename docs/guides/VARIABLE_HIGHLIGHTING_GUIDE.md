# Variable Highlighting Guide

**PostMini v1.7.1** | Enhanced Variable Visibility & Code Quality

---

## 📋 Overview

PostMini provides comprehensive variable highlighting throughout the application to help you easily identify and work with variables in your API requests. This guide explains all the variable highlighting features and how to use them effectively.

---

## 🎨 Variable Highlighting Features

### 1. **Inline Variable Highlighting**

Variables in the format `{{variableName}}` are automatically highlighted in:
- **URL field**
- **Headers table** (keys and values)
- **Query parameters table** (keys and values)
- **Request body editor**
- **Authorization token fields**

**Visual Indicators (v1.7.2+):**
- **🟢 Green**: Variable is defined and has a value
  - Dark Theme: `#4CAF50`
  - Light Theme: `#2E7D32`
- **🔴 Red**: Variable is undefined or missing  
  - Dark Theme: `#F44336`
  - Light Theme: `#D32F2F`

This color-coding helps you instantly identify which variables need attention before sending requests!

### 2. **Hover Tooltips**

When you hover over a variable, PostMini shows its current value in a tooltip:

```
{{baseUrl}}
  ↓ Hover
💡 baseUrl
   https://api.example.com/v1
```

**Tooltip shows:**
- Variable name
- Current resolved value
- "❌ Undefined" if the variable doesn't exist

**Works with:**
- ✅ Environment variables
- ✅ Collection variables
- ✅ Extracted variables (`{{extracted.variableName}}`)
- ✅ All variable scopes

### 3. **Table Cell Highlighting**

In the Headers and Params tables:
- Variables are highlighted **while viewing**
- Variables are highlighted **while editing**
- Seamless transition between view and edit modes
- Full theme support (dark/light)

### 4. **Variable Resolution Hierarchy**

PostMini resolves variables in this order (highest to lowest priority):

1. **🔗 Extracted Variables** - From "Extract Variables" tab
   - Syntax: `{{extracted.variableName}}`
   - Source: Extracted from API responses
   - Scope: Session-wide, persists across tabs

2. **🌍 Environment Variables** - From active environment
   - Syntax: `{{variableName}}`
   - Source: Selected environment
   - Scope: All requests when environment is active

3. **📦 Collection Variables** - From current collection
   - Syntax: `{{variableName}}`
   - Source: Collection settings
   - Scope: All requests in that collection

4. **⚡ Dynamic Variables** - Always available
   - Syntax: `$variableName`
   - Source: Auto-generated
   - Examples: `$guid`, `$timestamp`, `$randomEmail`

---

## 💡 Usage Examples

### Example 1: Environment Variables

```
URL: {{baseUrl}}/users/{{userId}}
```

**When environment "Development" is selected:**
- `baseUrl` → `https://dev-api.example.com`
- `userId` → `12345`
- **Result**: `https://dev-api.example.com/users/12345`

**Highlighting:**
- Both `{{baseUrl}}` and `{{userId}}` are highlighted in purple
- Hover over each to see their values

### Example 2: Extracted Variables

```
Headers:
Authorization: Bearer {{extracted.authToken}}
```

**After extracting token from login response:**
- `{{extracted.authToken}}` is highlighted
- Hover shows the actual token value
- Variable persists across all tabs and requests

### Example 3: Dynamic Variables

```
Body:
{
  "id": "$guid",
  "timestamp": "$timestamp",
  "email": "$randomEmail"
}
```

**Each request generates new values:**
- `$guid` → `a3f2e8d1-4b5c-6789-0123-456789abcdef`
- `$timestamp` → `1729123456`
- `$randomEmail` → `user12345@example.com`

**Highlighting:**
- Dynamic variables are highlighted in the body editor
- Hover to see they'll be auto-generated

---

## 🎯 Best Practices

### 1. **Use Descriptive Variable Names**

❌ **Bad:**
```
{{u}}/{{r}}/{{i}}
```

✅ **Good:**
```
{{baseUrl}}/{{resourcePath}}/{{itemId}}
```

**Why:** Clear names make it easy to identify variables at a glance, even without hovering.

### 2. **Leverage Variable Hierarchy**

```
# Collection variable (applies to all requests in collection)
apiKey = "collection-level-key"

# Environment variable (overrides collection for this environment)
apiKey = "environment-specific-key"

# Extracted variable (highest priority)
extracted.apiKey = "dynamically-extracted-key"
```

**Result:** The extracted variable wins, then environment, then collection.

### 3. **Use Extracted Variables for Chaining**

**Step 1: Login Request**
```
POST {{baseUrl}}/auth/login
Body: { "username": "user", "password": "pass" }
```

**Step 2: Extract Token**
- Click on `token` value in response
- Save as `{{extracted.authToken}}`

**Step 3: Use in Subsequent Requests**
```
GET {{baseUrl}}/protected/data
Headers:
  Authorization: Bearer {{extracted.authToken}}
```

**Benefit:** The token is highlighted and you can hover to verify it's correct.

### 4. **Check Undefined Variables**

Before sending a request:
1. Look for highlighted variables
2. Hover over each one
3. If you see "❌ Undefined", fix it:
   - Add to environment
   - Add to collection variables
   - Extract from a previous response
   - Check for typos

---

## 🔧 Technical Details

### Variable Highlighting Implementation

PostMini uses three specialized classes for variable highlighting:

1. **`HighlightedLineEdit`** - For single-line input fields
   - Custom paint event for highlighting
   - Mouse tracking for hover tooltips
   - Works with URL field and auth token fields

2. **`VariableSyntaxHighlighter`** - For multi-line text editors
   - QSyntaxHighlighter for QTextEdit widgets
   - Real-time highlighting as you type
   - Works with request body editor

3. **`VariableHighlightDelegate`** - For table cells
   - Custom delegate for table views
   - Highlights in both view and edit modes
   - Works with Headers and Params tables

### Performance Optimization

- Highlighting is done during paint events (no performance impact on typing)
- Regular expression pattern: `\{\{[^}]+\}\}`
- Tooltip lookups are cached by the environment manager
- No network calls during highlighting

---

## 🎨 Theme Support

Variable highlighting automatically adapts to your theme:

### Dark Theme
- Variable color: `#C792EA` (soft purple)
- Background highlight: Semi-transparent purple
- High contrast for readability

### Light Theme
- Variable color: `#7C4DFF` (vibrant purple)
- Background highlight: Subtle purple tint
- Optimized for light backgrounds

**To toggle theme:**
- Click the moon/sun icon in the toolbar
- Theme preference is saved automatically
- All variable highlighting updates instantly

---

## 📊 Variable Inspector

For a comprehensive view of all variables:

1. Click **"📊 Variables"** button in toolbar
2. View all variables grouped by scope:
   - 🔗 Extracted Variables
   - 🌍 Environment Variables
   - 📦 Collection Variables
   - ⚡ Dynamic Variables

3. Click any variable to copy its syntax
4. Search/filter to find specific variables

---

## 🐛 Troubleshooting

### Variable Not Highlighting?

**Check:**
1. ✅ Variable uses correct syntax: `{{variableName}}`
2. ✅ No spaces inside braces: `{{name}}` not `{{ name }}`
3. ✅ Braces are properly matched (2 opening, 2 closing)
4. ✅ For extracted variables: `{{extracted.name}}`

### Tooltip Shows "❌ Undefined"?

**Solutions:**
1. **Add to Environment**: Manage Environments → Add variable
2. **Add to Collection**: Right-click collection → Manage Variables
3. **Extract from Response**: Click value in Extract Variables tab
4. **Check Spelling**: Ensure variable name matches exactly

### Variable Not Substituting?

**Verify:**
1. ✅ Environment is selected (if using environment variables)
2. ✅ Variable exists in selected environment
3. ✅ Collection variables are saved
4. ✅ Extracted variables are in the Variable Library
5. ✅ Check Variable Inspector to see what's available

---

## 🆕 What's New

### v1.7.2 - Smart Variable Status

- **Color-coded variables** based on definition status:
  - 🟢 **Green** = Variable is defined and ready to use
  - 🔴 **Red** = Variable is undefined and needs attention
- **Instant validation** - Spot missing variables before sending requests
- **Real-time updates** - Colors change as you add/remove variables
- **All sources checked** - Environment, Collection, Extracted, and Dynamic variables

### v1.7.1 - Code Quality Improvements

- **Removed duplicate class definition** in `VariableHighlightDelegate`
- **Added margin: 0px** to editor stylesheets for cleaner table editing
- **Improved code maintainability** and reduced technical debt
- **All tests passing** (50+ tests verified)

### Enhanced Styling

- Better separation between variable types
- Improved contrast in both themes
- More consistent highlighting across all input types

---

## 📚 Related Features

- **[Variable Status Highlighting](VARIABLE_STATUS_HIGHLIGHTING.md)** - 🆕 Green/Red color coding
- **[Environment Variables Guide](ENVIRONMENT_VARIABLES_GUIDE.md)** - Managing environments
- **[QA Features Guide](QA_FEATURES_GUIDE.md)** - Variable extraction and testing
- **[Dynamic Variables](../README.md#using-dynamic-variables-v140)** - Auto-generated variables

---

## ✅ Quick Reference Card

| Variable Type | Syntax | Where to Define | Priority |
|--------------|--------|-----------------|----------|
| Extracted | `{{extracted.name}}` | Extract Variables tab | 🥇 Highest |
| Environment | `{{name}}` | Manage Environments | 🥈 High |
| Collection | `{{name}}` | Collection → Manage Variables | 🥉 Medium |
| Dynamic | `$name` | Auto-generated | 📊 Lowest |

**Highlighting Colors (v1.7.2+):**
- 🟢 **Green** = Defined (Dark: `#4CAF50`, Light: `#2E7D32`)
- 🔴 **Red** = Undefined (Dark: `#F44336`, Light: `#D32F2F`)

**Tooltip:** Hover over any variable to see its value

**Status Indicator:** Variables change color based on whether they're defined!

---

**Happy API Testing! 🚀**

*PostMini v1.7.1 - Enhanced Variable Visibility*

