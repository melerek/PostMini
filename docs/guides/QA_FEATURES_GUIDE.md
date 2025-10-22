# PostMini - QA Features Guide

**Version:** 1.7.0  
**For:** Quality Assurance Engineers  
**Date:** October 22, 2025

---

## 🎯 New Features for QA Engineers

PostMini v1.7.0 introduces two powerful features specifically designed for QA workflows:

1. **🔗 Request Chaining & Variable Extraction** - Extract values from responses and use them in subsequent requests
2. **📊 Advanced Test Reporting** - Export test results in multiple formats (HTML, JUnit XML, JSON, CSV)

---

## 🔗 Feature 1: Request Chaining & Variable Extraction

### What Is Request Chaining?

Request chaining allows you to **extract values from API responses** and **automatically use them in subsequent requests**. This is essential for testing workflows like:

- Login → Get token → Use token in protected endpoints
- Create resource → Get ID → Update/Delete the resource
- Multi-step workflows requiring data from previous steps

### How to Use Request Chaining

#### Step 1: Send a Request

1. Open or create a request (e.g., `POST /login`)
2. Configure the request (method, URL, body, etc.)
3. Click **Send** to execute the request

#### Step 2: Extract Variables from Response

After receiving a response:

1. Click the **"Extract Variables"** tab in the response section
2. You'll see:
   - 📊 **JSON Tree View** - Browse the entire response structure
   - 💡 **Quick Suggestions** - Automatically suggested variables to extract
   
3. **To extract a variable:**
   - **Option A:** Click any value in the JSON tree
   - **Option B:** Select a suggested variable from the dropdown
   
4. Fill in the extraction form:
   - **Variable Name:** e.g., `authToken`, `userId`, `orderId`
   - **JSON Path:** Auto-filled when you click a value (e.g., `data.token`)
   - **Extracted Value:** Shows the actual value being extracted
   - **Description:** Optional note about what this variable is for

5. Click **💾 Save Variable**

#### Step 3: Use Extracted Variables in Requests

Once saved, use extracted variables in any request using this syntax:

```
{{extracted.variableName}}
```

**Examples:**

```
URL:
GET https://api.example.com/users/{{extracted.userId}}

Headers:
Authorization: Bearer {{extracted.authToken}}

Body:
{
  "orderId": "{{extracted.orderId}}",
  "token": "{{extracted.sessionToken}}"
}
```

#### Step 4: View All Extracted Variables

Click the **"📚 Variable Library"** button in the sidebar to:
- View all extracted variables
- See their values and source requests
- Copy variable references (`{{extracted.variableName}}`)
- Delete variables you no longer need

### Real-World Example: Login Flow

**Request 1: Login**
```
POST /api/auth/login
Body:
{
  "email": "qa@example.com",
  "password": "test123"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "token": "eyJhbGciOiJ...",
    "userId": 12345,
    "expiresIn": 3600
  }
}
```

**Extract Variables:**
1. Click `data.token` → Save as `authToken`
2. Click `data.userId` → Save as `userId`

**Request 2: Get User Profile (uses extracted variables)**
```
GET /api/users/{{extracted.userId}}
Headers:
  Authorization: Bearer {{extracted.authToken}}
```

**Request 3: Update Profile (uses extracted variables)**
```
PUT /api/users/{{extracted.userId}}
Headers:
  Authorization: Bearer {{extracted.authToken}}
Body:
{
  "name": "New Name"
}
```

### Tips & Best Practices

✅ **DO:**
- Use descriptive variable names (`authToken`, `userId`, not `var1`, `x`)
- Extract variables immediately after receiving responses
- Add descriptions to document what each variable is for
- Review the Variable Library regularly to clean up old variables

❌ **DON'T:**
- Use special characters in variable names (only letters, numbers, underscore)
- Forget to check that extracted values are correct before using them
- Extract complex objects (extract primitive values like strings/numbers)

### Variable Resolution Order

PostMini resolves variables in this order:

1. **Extracted Variables** (`{{extracted.variableName}}`)
2. **Collection Variables** (`{{variableName}}`)
3. **Environment Variables** (`{{variableName}}`)
4. **Dynamic Variables** (`$variableName`)

This means extracted variables have the highest priority and will override environment/collection variables if there's a conflict.

---

## 📊 Feature 2: Advanced Test Reporting

### What Is Test Reporting?

Test reporting allows you to **export test results** in multiple formats for:
- Sharing with stakeholders
- CI/CD pipeline integration
- Automated processing
- Documentation and compliance

### Supported Export Formats

| Format | Use Case | Best For |
|--------|----------|----------|
| **📄 HTML** | Beautiful, shareable reports | Stakeholders, managers, documentation |
| **📋 JUnit XML** | CI/CD integration | Jenkins, GitLab CI, GitHub Actions |
| **🔧 JSON** | Machine-readable | Automation scripts, custom processing |
| **📊 CSV** | Spreadsheet analysis | Excel, data analysis |

### How to Export Test Reports

#### Step 1: Run Tests on a Collection

1. Right-click a collection in the sidebar
2. Select **"Run Tests"**
3. Click **▶️ Run Tests** in the dialog
4. Wait for tests to complete

#### Step 2: Export Results

After tests complete, export buttons become enabled:

**Export as HTML Report:**
1. Click **📄 Export HTML**
2. Choose save location
3. Click **Yes** to open in browser automatically

**Export as JUnit XML:**
1. Click **📋 Export JUnit XML**
2. Choose save location
3. Use the XML file in your CI/CD pipeline

**Export as JSON:**
1. Click **🔧 Export JSON**
2. Choose save location
3. Process with custom scripts

### HTML Report Features

The HTML report includes:

**Summary Dashboard:**
- Total tests count
- Passed/Failed breakdown
- Pass rate percentage
- Metadata (collection name, environment, timestamp)

**Failed Tests Section:**
- ❌ Clear indication of failures
- Expected vs Actual values
- Error messages with suggestions
- Expandable details

**Passed Tests Section:**
- ✅ Collapsible list of passing tests
- Actual values for verification
- Test details

**Interactive Features:**
- Click to expand/collapse sections
- Responsive design (works on mobile)
- Professional styling
- Copy-friendly formatting

### JUnit XML for CI/CD

The JUnit XML format is compatible with:
- Jenkins
- GitLab CI/CD
- GitHub Actions
- Azure DevOps
- CircleCI
- Travis CI
- Any CI tool that supports JUnit XML

**Example Integration (GitLab CI):**

```yaml
test_api:
  script:
    - postmini run-collection "My API Tests"
  artifacts:
    reports:
      junit: junit_*.xml
```

### JSON Report Structure

```json
{
  "summary": {
    "total": 50,
    "passed": 48,
    "failed": 2,
    "pass_rate": 96.0
  },
  "metadata": {
    "collection_name": "API Tests",
    "environment": "Production",
    "timestamp": "2025-10-22T14:32:15"
  },
  "tests": [
    {
      "name": "status_code: equals",
      "passed": true,
      "type": "status_code",
      "operator": "equals",
      "expected_value": "200",
      "actual_value": "200"
    }
  ]
}
```

### Real-World Workflow

**Scenario:** QA needs to verify API changes and report to the team

1. **Run Tests:**
   - Right-click "User API" collection
   - Select "Run Tests"
   - Wait for completion

2. **Export HTML for Team:**
   - Click "📄 Export HTML"
   - Save as `user_api_test_results_2025-10-22.html`
   - Email to team or attach to ticket

3. **Export JUnit for CI:**
   - Click "📋 Export JUnit XML"
   - Save as `junit_user_api.xml`
   - Commit to repository for automated testing

4. **Export JSON for Analysis:**
   - Click "🔧 Export JSON"
   - Process with Python script to track trends

### Tips & Best Practices

✅ **DO:**
- Export reports immediately after test runs
- Include collection name and environment in filenames
- Store historical reports for trend analysis
- Share HTML reports with non-technical stakeholders
- Use JUnit XML in CI/CD pipelines
- Archive reports for compliance/audit purposes

❌ **DON'T:**
- Forget to run tests before exporting (buttons are disabled)
- Overwrite previous reports without backing them up
- Share reports with sensitive data (tokens, passwords)

---

## 🔄 Combined Workflow: Request Chaining + Test Reporting

Here's a complete QA workflow combining both features:

### Scenario: Testing User Management API

**Step 1: Create User & Extract ID**
```
POST /api/users
Body: {"name": "Test User", "email": "test@example.com"}

Response:
{
  "id": 789,
  "name": "Test User",
  "email": "test@example.com"
}

Extract: userId = 789
```

**Step 2: Verify User Creation**
```
GET /api/users/{{extracted.userId}}

Tests:
- Status Code equals 200
- JSON Path "name" equals "Test User"
- JSON Path "id" equals {{extracted.userId}}
```

**Step 3: Update User**
```
PUT /api/users/{{extracted.userId}}
Body: {"name": "Updated Name"}

Tests:
- Status Code equals 200
- JSON Path "name" equals "Updated Name"
```

**Step 4: Delete User**
```
DELETE /api/users/{{extracted.userId}}

Tests:
- Status Code equals 204
```

**Step 5: Verify Deletion**
```
GET /api/users/{{extracted.userId}}

Tests:
- Status Code equals 404
```

**Step 6: Run Tests & Export Report**
1. Right-click collection → Run Tests
2. Review results (all 10+ assertions)
3. Export HTML report for documentation
4. Export JUnit XML for CI pipeline

---

## 🎓 Advanced Tips

### Variable Naming Conventions

```
✅ GOOD:
- {{extracted.authToken}}
- {{extracted.userId}}
- {{extracted.orderId}}
- {{extracted.sessionId}}

❌ BAD:
- {{extracted.token}}  (ambiguous)
- {{extracted.id}}     (what kind of ID?)
- {{extracted.x}}      (meaningless)
- {{extracted.temp}}   (temporary variable names)
```

### Organizing Test Reports

**Recommended File Structure:**
```
reports/
├── 2025-10-22/
│   ├── user_api_tests.html
│   ├── user_api_tests_junit.xml
│   └── user_api_tests.json
├── 2025-10-21/
│   └── ...
└── archives/
    └── older_reports/
```

### CI/CD Integration Example

**Jenkins Pipeline:**
```groovy
pipeline {
    agent any
    stages {
        stage('API Tests') {
            steps {
                sh 'postmini run-tests'
            }
        }
    }
    post {
        always {
            junit '**/junit_*.xml'
            archiveArtifacts '**/*.html'
        }
    }
}
```

---

## ❓ Troubleshooting

### Variable Extraction Issues

**Problem:** "Variable not found" error when using `{{extracted.varName}}`

**Solutions:**
1. Check Variable Library to confirm variable exists
2. Verify spelling (case-sensitive)
3. Ensure you used `{{extracted.varName}}` syntax (not `{{varName}}`)

**Problem:** Extracted value is empty or wrong

**Solutions:**
1. Verify the JSON path is correct
2. Check response structure in Response tab
3. Re-extract the variable with correct path

### Report Export Issues

**Problem:** Export buttons are disabled

**Solutions:**
1. Run tests first (click "▶️ Run Tests")
2. Wait for tests to complete
3. Ensure tests actually ran (check log)

**Problem:** HTML report doesn't open

**Solutions:**
1. Check that file was saved successfully
2. Right-click file → Open With → Browser
3. Check file permissions

---

## 📞 Support & Feedback

Have questions or suggestions? Please:
- Check the main README.md
- Open an issue on GitHub
- Contact the development team

---

**Happy Testing! 🚀**

*PostMini - Professional API Testing Made Simple*

