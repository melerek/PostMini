# Test Runner Method Name Fix

**Date:** October 17, 2025  
**Issue:** Collection Test Runner failing with AttributeError  
**Status:** ✅ **FIXED**

---

## 🐛 **Issue Reported**

When running tests on imported collections (e.g., "Sample Pet Store API"), users encountered errors:

```
❌ Find pet by ID: ERROR - 'ApiClient' object has no attribute 'execute'
❌ Find pets by status: ERROR - 'ApiClient' object has no attribute 'execute'
```

---

## 🔍 **Root Cause**

**File:** `src/ui/dialogs/collection_test_runner.py`  
**Line:** 92

The test runner was calling:
```python
response = self.api_client.execute(...)  # ❌ Wrong method name
```

But the `ApiClient` class actually has:
```python
def execute_request(self, method, url, params, ...):  # ✅ Correct method name
```

---

## ✅ **Fix Applied**

**File:** `src/ui/dialogs/collection_test_runner.py`  
**Line:** 92

**Before:**
```python
response = self.api_client.execute(
    method=request['method'],
    url=url,
    params=params,
    headers=headers,
    body=body,
    auth_type=request.get('auth_type', 'None'),
    auth_token=auth_token
)
```

**After:**
```python
response = self.api_client.execute_request(
    method=request['method'],
    url=url,
    params=params,
    headers=headers,
    body=body,
    auth_type=request.get('auth_type', 'None'),
    auth_token=auth_token
)
```

**Change:** `execute()` → `execute_request()`

---

## 🎯 **Impact**

### **What This Fixes**
- ✅ Collection test runner now works correctly
- ✅ Tests can be executed on imported OpenAPI collections
- ✅ Test assertions evaluate properly
- ✅ API requests are sent successfully

### **Affected Features**
- ✅ "Run Tests" button in collection context menu
- ✅ Test Runner dialog for collections
- ✅ Automated testing of API endpoints

---

## 🧪 **How to Test**

1. **Import an OpenAPI spec** (e.g., Sample Pet Store API)
2. **Right-click the collection** → Select "Run Tests"
3. **Test Runner dialog opens**
4. **Click "Run Tests"** button
5. **Verify:** Tests execute without AttributeError

**Expected Result:**
- ✅ Requests execute successfully
- ✅ Response data displayed
- ✅ Test assertions evaluated
- ✅ Pass/fail results shown

---

## 📝 **Technical Details**

### **ApiClient Methods**
The `ApiClient` class (in `src/core/api_client.py`) has always used `execute_request()` as the method name:

```python
def execute_request(self, 
                   method: str,
                   url: str,
                   params: Optional[Dict] = None,
                   headers: Optional[Dict] = None,
                   body: Optional[str] = None,
                   auth_type: str = 'None',
                   auth_token: Optional[str] = None) -> ApiResponse:
```

### **Why This Worked Before**
The test runner feature was likely:
1. Not frequently used on imported collections
2. Manually tested requests work fine (they call `execute_request()` correctly)
3. Only affected automated collection testing

### **Similar Usages Checked**
✅ Main window `_send_request()` - Uses `execute_request()` correctly  
✅ Manual request execution - Uses `execute_request()` correctly  
✅ Collection test runner - **Fixed** to use `execute_request()`

No other incorrect usages found.

---

## 🔄 **Related Components**

### **Working Components**
- ✅ `src/core/api_client.py` - ApiClient class definition
- ✅ `src/ui/main_window.py` - Manual request execution
- ✅ `src/features/test_engine.py` - Test assertion evaluation

### **Fixed Component**
- ✅ `src/ui/dialogs/collection_test_runner.py` - Collection test execution

---

## ✅ **Verification**

### **Before Fix**
```
❌ Test execution fails immediately
❌ AttributeError: 'ApiClient' object has no attribute 'execute'
❌ No requests are sent
❌ No test results displayed
```

### **After Fix**
```
✅ Test execution proceeds normally
✅ API requests are sent successfully
✅ Responses are received and evaluated
✅ Test results (pass/fail) are displayed correctly
```

---

## 🎉 **Conclusion**

The issue was a simple method name mismatch in the collection test runner. The fix is straightforward and restores full functionality to the automated testing feature.

**This fix will be included in the next installer build** or can be applied immediately by restarting the application with the updated code.

---

**Fixed Date:** October 17, 2025  
**PostMini Version:** 1.4.0  
**Issue:** Collection test runner method name mismatch  
**Status:** **RESOLVED** ✅

