# Code Generation - User Guide

## Overview

The Code Generation feature allows you to instantly generate ready-to-use code snippets in multiple programming languages from your API requests. Perfect for:
- 📋 **Quick Integration** - Copy-paste into your application
- 👥 **Team Documentation** - Share working examples
- 🚀 **Faster Development** - No manual code writing
- 📚 **Learning** - See how to make requests in different languages

## Supported Languages

✅ **curl** (Command Line)  
✅ **Python** (requests library)  
✅ **JavaScript** (fetch API)  
✅ **JavaScript** (axios library)  
✅ **Node.js** (https module)  
✅ **React** (Component with hooks)  
✅ **C#** (HttpClient)  

---

## How to Use

### Step 1: Configure Your Request

1. Set up your request in the main window:
   - Method (GET, POST, etc.)
   - URL
   - Query parameters (Params tab)
   - Headers (Headers tab)
   - Request body (Body tab)
   - Authentication (Authorization tab)

2. You don't need to send the request first!

### Step 2: Generate Code

1. Click the **"💻 Code"** button (next to Save button)
2. Code Generation dialog opens
3. Default language is curl

### Step 3: Select Language

1. Use the **"Language:"** dropdown
2. Select your desired language
3. Code updates instantly!

### Step 4: Copy Code

1. Review the generated code
2. Click **"📋 Copy to Clipboard"** button
3. Success message appears
4. Paste into your application!

---

## Code Examples

### Example 1: Simple GET Request

**Your Configuration:**
```
Method: GET
URL: https://api.example.com/users
```

**Generated curl:**
```bash
curl --request GET \
  --url 'https://api.example.com/users'
```

**Generated Python:**
```python
import requests

url = "https://api.example.com/users"

response = requests.get(url)

print(f'Status Code: {response.status_code}')
print(f'Response: {response.text}')
```

**Generated JavaScript (fetch):**
```javascript
const url = 'https://api.example.com/users';

const options = {
  method: 'GET',
};

fetch(url, options)
  .then(response => response.json())
  .then(data => console.log(data))
  .catch(error => console.error('Error:', error));
```

### Example 2: POST with JSON Body

**Your Configuration:**
```
Method: POST
URL: https://api.example.com/users
Headers:
  Content-Type: application/json
Body:
  {"name": "John Doe", "email": "john@example.com"}
```

**Generated Python:**
```python
import requests

url = "https://api.example.com/users"

headers = {
    "Content-Type": "application/json",
}

data = {
    "name": "John Doe",
    "email": "john@example.com"
}

response = requests.post(url, headers=headers, data=data)

print(f'Status Code: {response.status_code}')
print(f'Response: {response.text}')
```

**Generated React:**
```jsx
import React, { useState, useEffect } from 'react';

function ApiComponent() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch('https://api.example.com/users', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({"name":"John Doe","email":"john@example.com"}),
        });

        if (!response.ok) {
          throw new Error('Network response was not ok');
        }

        const result = await response.json();
        setData(result);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error}</div>;

  return (
    <div>
      <h2>API Response</h2>
      <pre>{JSON.stringify(data, null, 2)}</pre>
    </div>
  );
}

export default ApiComponent;
```

### Example 3: Request with Authentication

**Your Configuration:**
```
Method: GET
URL: https://api.example.com/protected
Authorization: Bearer Token
Token: your-secret-token-123
```

**Generated curl:**
```bash
curl --request GET \
  --url 'https://api.example.com/protected' \
  --header 'Authorization: Bearer your-secret-token-123'
```

**Generated C#:**
```csharp
using System;
using System.Net.Http;
using System.Text;
using System.Threading.Tasks;

class Program
{
    static async Task Main()
    {
        using (var client = new HttpClient())
        {
            client.DefaultRequestHeaders.Add("Authorization", "Bearer your-secret-token-123");

            var response = await client.GetAsync("https://api.example.com/protected");

            var responseBody = await response.Content.ReadAsStringAsync();
            Console.WriteLine($"Status: {response.StatusCode}");
            Console.WriteLine($"Response: {responseBody}");
        }
    }
}
```

### Example 4: Complex Request with Everything

**Your Configuration:**
```
Method: POST
URL: https://api.example.com/users
Params:
  limit: 10
  offset: 0
Headers:
  Content-Type: application/json
  X-API-Key: key123
Body:
  {"username": "john_doe", "email": "john@example.com"}
Authorization: Bearer Token
Token: secret_token
```

**Generated Python:**
```python
import requests

url = "https://api.example.com/users"

params = {
    "limit": "10",
    "offset": "0",
}

headers = {
    "Content-Type": "application/json",
    "X-API-Key": "key123",
    "Authorization": "Bearer secret_token",
}

data = {
    "username": "john_doe",
    "email": "john@example.com"
}

response = requests.post(url, params=params, headers=headers, data=data)

print(f'Status Code: {response.status_code}')
print(f'Response: {response.text}')
```

---

## Language-Specific Notes

### curl (Command Line)
- **Use Case**: Quick testing, scripts, CI/CD
- **Copy**: Paste directly into terminal
- **Note**: Multi-line format with `\` for readability

### Python (requests)
- **Use Case**: Python applications, data science, automation
- **Requires**: `pip install requests`
- **Format**: Clean, readable code with proper imports

### JavaScript (fetch)
- **Use Case**: Browser applications, modern web apps
- **Native**: No external libraries needed
- **Async**: Uses promises (.then/.catch)

### JavaScript (axios)
- **Use Case**: Node.js and browser apps
- **Requires**: `npm install axios`
- **Features**: Better error handling, interceptors

### Node.js (https)
- **Use Case**: Server-side Node.js applications
- **Native**: Uses built-in https module
- **No Dependencies**: Pure Node.js

### React (Component)
- **Use Case**: React applications
- **Includes**: useState, useEffect hooks
- **Features**: Loading states, error handling
- **Ready**: Complete functional component

### C# (HttpClient)
- **Use Case**: .NET applications
- **Framework**: .NET Core / .NET 5+
- **Async**: Uses async/await pattern
- **Production**: Uses HttpClient best practices

---

## Use Cases

### 1. Quick Integration

**Scenario**: Need to integrate API into your app

**Workflow:**
1. Test request in API Client
2. Generate code in your language
3. Copy to your application
4. Customize as needed
5. Done in minutes!

**Time Saved:** 10-30 minutes per endpoint

### 2. Team Documentation

**Scenario**: Document API usage for team

**Workflow:**
1. Create example requests
2. Generate code for all languages
3. Add to team documentation
4. Team has working examples

**Benefit:** No more "how do I call this API?" questions

### 3. Learning Different Languages

**Scenario:** Want to learn API calls in new language

**Workflow:**
1. Configure request
2. Generate code in new language
3. Study the syntax
4. Understand patterns

**Benefit:** See real examples instantly

### 4. Client Library Creation

**Scenario:** Building API wrapper library

**Workflow:**
1. Design API endpoints
2. Generate code for each
3. Use as base for library
4. Refactor and enhance

**Benefit:** Faster library development

### 5. Testing Automation

**Scenario:** Create automated API tests

**Workflow:**
1. Test API manually
2. Generate Python/Node.js code
3. Convert to test cases
4. Add assertions

**Benefit:** Automated test suite quickly

---

## Tips & Tricks

### Tip 1: Variables Work!

If you use environment variables like `{{baseUrl}}`, the generated code will include the substituted values:

```
URL: {{baseUrl}}/users
With Environment "Development" active:
Generated Code will have: https://dev-api.example.com/users
```

### Tip 2: Test First, Generate Later

1. Send request to verify it works
2. Check response is correct
3. Then generate code
4. You know the code will work!

### Tip 3: Customize After Copying

Generated code is a starting point:
- Add error handling
- Customize response processing
- Add retry logic
- Integrate with your architecture

### Tip 4: Multiple Languages for Team

If your team uses multiple languages:
1. Generate for all languages
2. Save in documentation
3. Everyone has their preferred language

### Tip 5: Use with History

1. Find working request in History
2. Replay it
3. Generate code
4. Perfect working example!

---

## Keyboard Workflow (Future)

Coming soon:
- `Ctrl+Shift+C` - Open Code Generator
- `Ctrl+C` - Copy code (in dialog)
- Arrow keys - Switch languages

---

## FAQ

**Q: Do I need to send the request first?**  
A: No! You can generate code before sending.

**Q: Can I modify the generated code?**  
A: Yes! It's a starting point. Customize as needed.

**Q: Are environment variables included?**  
A: The substituted values are included in generated code.

**Q: What if I need a different language?**  
A: Request it! We may add more languages in future.

**Q: Can I save generated code?**  
A: Copy to clipboard, then save in your project.

**Q: Does it work with complex requests?**  
A: Yes! All params, headers, body, auth are included.

**Q: Are there any limitations?**  
A: File uploads and multipart forms may need manual adjustment.

**Q: Can I generate code from History?**  
A: Yes! Replay from History, then generate.

---

## Troubleshooting

### Issue: Generated code doesn't work

**Possible Causes:**
1. URL has environment variables not substituted
2. Missing dependencies in target language
3. API requires additional setup

**Solutions:**
- Select correct environment first
- Install required libraries
- Check API documentation for requirements

### Issue: Can't copy to clipboard

**Possible Causes:**
1. Clipboard access denied
2. Very long code

**Solutions:**
- Check system permissions
- Manually select and copy text

### Issue: Code format looks wrong

**Possible Causes:**
1. Font settings
2. Line wrap enabled

**Solutions:**
- Dialog uses monospace font
- Copy and paste into proper editor

---

## Best Practices

### ✅ DO:

1. **Test Before Generating**
   - Verify request works
   - Check response is correct

2. **Select Correct Environment**
   - Ensures correct URLs
   - Proper API keys

3. **Review Generated Code**
   - Check it looks right
   - Understand what it does

4. **Customize for Production**
   - Add error handling
   - Add logging
   - Add retries

5. **Keep Updated**
   - If request changes
   - Regenerate code

### ❌ DON'T:

1. **Don't Use Without Testing**
   - Generated code untested
   - May need adjustments

2. **Don't Share Sensitive Tokens**
   - Review before sharing
   - Remove real tokens

3. **Don't Expect Perfect Code**
   - It's a starting point
   - Needs customization

4. **Don't Ignore Errors**
   - Add proper error handling
   - Don't skip validation

---

## Examples by Language

### curl Examples

**GET with Headers:**
```bash
curl --request GET \
  --url 'https://api.example.com/users' \
  --header 'Authorization: Bearer token' \
  --header 'Accept: application/json'
```

**POST with JSON:**
```bash
curl --request POST \
  --url 'https://api.example.com/users' \
  --header 'Content-Type: application/json' \
  --data '{"name":"John","age":30}'
```

### Python Examples

**Simple GET:**
```python
response = requests.get("https://api.example.com/users")
print(response.json())
```

**POST with Auth:**
```python
headers = {"Authorization": "Bearer token"}
data = {"name": "John"}
response = requests.post("https://api.example.com/users", 
                         headers=headers, json=data)
```

### JavaScript Examples

**Fetch with Async/Await:**
```javascript
async function fetchData() {
  const response = await fetch('https://api.example.com/users');
  const data = await response.json();
  console.log(data);
}
```

**Axios with Error Handling:**
```javascript
axios.get('https://api.example.com/users')
  .then(response => console.log(response.data))
  .catch(error => console.error(error));
```

---

## Integration Examples

### React Hook Example

```jsx
// Custom hook generated from your request
function useApi() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('https://api.example.com/users')
      .then(r => r.json())
      .then(setData)
      .finally(() => setLoading(false));
  }, []);

  return { data, loading };
}
```

### Python Class Example

```python
# Generated code as class method
class ApiClient:
    def get_users(self):
        response = requests.get("https://api.example.com/users")
        return response.json()
```

---

## Support

Need help?
1. Check this guide
2. Review generated code
3. Test in your environment
4. Check language documentation

---

**Happy Coding with Code Generation! 💻🚀**

