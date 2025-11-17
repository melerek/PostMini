"""
JavaScript Script Snippets Library

Pre-built script examples for common use cases in pre-request and post-response scripts.
"""

from typing import Dict, List


class ScriptSnippets:
    """Collection of JavaScript code snippets for common scripting tasks."""
    
    PRE_REQUEST_SNIPPETS = {
        "Set Timestamp": {
            "description": "Add current Unix timestamp to environment",
            "code": """// Set current timestamp
const timestamp = Date.now();
pm.environment.set("timestamp", timestamp);
console.log("Timestamp set: " + timestamp);"""
        },
        
        "Generate UUID": {
            "description": "Generate a unique request ID",
            "code": """// Generate unique UUID
const uuid = 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
    const r = Math.random() * 16 | 0;
    const v = c === 'x' ? r : (r & 0x3 | 0x8);
    return v.toString(16);
});
pm.environment.set("requestId", uuid);
console.log("Request ID: " + uuid);"""
        },
        
        "Set Dynamic Header": {
            "description": "Add a dynamic header to the request",
            "code": """// Add custom header with timestamp
const value = "Bearer " + pm.environment.get("authToken");
pm.request.headers.add({
    key: "Authorization",
    value: value
});
console.log("Authorization header added");"""
        },
        
        "Basic Auth Encoding": {
            "description": "Encode username and password for Basic Auth",
            "code": """// Encode credentials for Basic Authentication
const username = pm.environment.get("username");
const password = pm.environment.get("password");
const credentials = username + ":" + password;
const encoded = btoa(credentials);

pm.request.headers.upsert({
    key: "Authorization",
    value: "Basic " + encoded
});
console.log("Basic Auth header added");"""
        },
        
        "Random String Generator": {
            "description": "Generate a random alphanumeric string",
            "code": """// Generate random string
function randomString(length) {
    const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
    let result = '';
    for (let i = 0; i < length; i++) {
        result += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    return result;
}

const randomStr = randomString(16);
pm.environment.set("randomString", randomStr);
console.log("Random string: " + randomStr);"""
        },
        
        "Current Date ISO": {
            "description": "Get current date in ISO format",
            "code": """// Get current date in ISO format
const isoDate = new Date().toISOString();
pm.environment.set("currentDate", isoDate);
console.log("Current date: " + isoDate);"""
        },
        
        "URL Parameter Builder": {
            "description": "Build dynamic URL with parameters",
            "code": """// Build URL with dynamic parameters
const baseUrl = pm.environment.get("baseUrl");
const userId = pm.environment.get("userId");
const newUrl = baseUrl + "/users/" + userId;

pm.request.url = newUrl;
console.log("URL updated: " + newUrl);"""
        },
        
        "Request Counter": {
            "description": "Track request count in environment",
            "code": """// Increment request counter
let count = pm.environment.get("requestCount");
count = count ? parseInt(count) + 1 : 1;
pm.environment.set("requestCount", count);
console.log("Request count: " + count);"""
        },
        
        "Conditional Headers": {
            "description": "Add headers based on conditions",
            "code": """// Add headers conditionally
const environment = pm.environment.get("env");

if (environment === "production") {
    pm.request.headers.add({
        key: "X-Environment",
        value: "prod"
    });
} else {
    pm.request.headers.add({
        key: "X-Environment",
        value: "dev"
    });
}"""
        },
        
        "HMAC Signature (Placeholder)": {
            "description": "Generate HMAC signature for request authentication",
            "code": """// Generate HMAC-SHA256 signature
// Note: Full crypto implementation requires additional libraries
const secret = pm.environment.get("apiSecret");
const message = pm.request.url + pm.request.body.raw;

// Placeholder - actual HMAC would use CryptoJS
const signature = "HMAC_SIGNATURE_PLACEHOLDER";
pm.request.headers.upsert({
    key: "X-Signature",
    value: signature
});

console.log("Signature added (placeholder)");"""
        },
        
        "Set Collection Variable": {
            "description": "Set a collection variable value",
            "code": """// Set collection variable
const orderId = pm.variables.replaceIn('{{$guid}}');
pm.collectionVariables.set('orderId', orderId);
console.log('Collection variable set: orderId = ' + orderId);"""
        },
        
        "Get Collection Variable": {
            "description": "Get a collection variable value",
            "code": """// Get collection variable
const orderId = pm.collectionVariables.get('orderId');
console.log('Collection variable: orderId = ' + orderId);

// Use in request
pm.request.headers.add({
    key: 'X-Order-Id',
    value: orderId
});"""
        }
    }
    
    POST_RESPONSE_SNIPPETS = {
        "Extract JSON Token": {
            "description": "Extract authentication token from JSON response",
            "code": """// Extract token from response
const jsonData = pm.response.json();
const token = jsonData.access_token || jsonData.token;

if (token) {
    pm.environment.set("authToken", token);
    console.log("Token saved: " + token.substring(0, 20) + "...");
} else {
    console.error("Token not found in response");
}"""
        },
        
        "Extract User Data": {
            "description": "Extract and save user information",
            "code": """// Extract user data from response
const response = pm.response.json();

if (response.data && response.data.user) {
    const user = response.data.user;
    pm.environment.set("userId", user.id);
    pm.environment.set("userName", user.name);
    pm.environment.set("userEmail", user.email);
    
    console.log("User data saved:");
    console.log("- ID: " + user.id);
    console.log("- Name: " + user.name);
}"""
        },
        
        "Status Code Test": {
            "description": "Validate response status code",
            "code": """// Test response status
pm.test("Status code is 200", function() {
    pm.expect(pm.response.code).to.equal(200);
});

pm.test("Status is OK", function() {
    pm.expect(pm.response.status).to.equal("OK");
});

console.log("Status: " + pm.response.code + " " + pm.response.status);"""
        },
        
        "Response Time Test": {
            "description": "Check if response time is acceptable",
            "code": """// Test response time
pm.test("Response time is less than 500ms", function() {
    pm.expect(pm.response.responseTime).to.be.below(500);
});

console.log("Response time: " + pm.response.responseTime + "ms");"""
        },
        
        "Set Collection Variable": {
            "description": "Set a collection variable from response",
            "code": """// Extract value from response and save to collection variable
const jsonData = pm.response.json();
const userId = jsonData.data.id;

pm.collectionVariables.set('userId', userId);
console.log('Collection variable set: userId = ' + userId);"""
        },
        
        "Get Collection Variable": {
            "description": "Get a collection variable value",
            "code": """// Get collection variable
const userId = pm.collectionVariables.get('userId');
console.log('Collection variable: userId = ' + userId);

// Use for validation
pm.test('User ID matches', function() {
    const responseId = pm.response.json().id;
    pm.expect(responseId).to.equal(userId);
});"""
        },
        
        "JSON Structure Test": {
            "description": "Validate JSON response structure",
            "code": """// Test JSON structure
pm.test("Response has required fields", function() {
    const jsonData = pm.response.json();
    pm.expect(jsonData).to.have.property("status");
    pm.expect(jsonData).to.have.property("data");
    pm.expect(jsonData.data).to.be.a("object");
});

console.log("JSON structure validated");"""
        },
        
        "Array Length Test": {
            "description": "Validate array length in response",
            "code": """// Test array length
pm.test("Response contains items", function() {
    const jsonData = pm.response.json();
    pm.expect(jsonData.items).to.be.a("array");
    pm.expect(jsonData.items.length).to.be.above(0);
});

const itemCount = pm.response.json().items.length;
console.log("Items in response: " + itemCount);"""
        },
        
        "Extract Nested Data": {
            "description": "Extract deeply nested values from JSON",
            "code": """// Extract nested data
const response = pm.response.json();

// Safely access nested properties
if (response.data && response.data.user && response.data.user.profile) {
    const profile = response.data.user.profile;
    pm.collectionVariables.set("userAvatar", profile.avatar);
    pm.collectionVariables.set("userBio", profile.bio);
    
    console.log("Profile data extracted");
}"""
        },
        
        "Header Validation": {
            "description": "Validate response headers",
            "code": """// Test response headers
pm.test("Content-Type is JSON", function() {
    const contentType = pm.response.headers.get("Content-Type");
    pm.expect(contentType).to.include("application/json");
});

pm.test("Has CORS headers", function() {
    pm.expect(pm.response.headers.has("Access-Control-Allow-Origin")).to.be.true;
});

console.log("Headers validated");"""
        },
        
        "Error Handling": {
            "description": "Handle error responses gracefully",
            "code": """// Handle error responses
if (pm.response.code >= 400) {
    const error = pm.response.json();
    console.error("Request failed:");
    console.error("- Status: " + pm.response.code);
    console.error("- Message: " + (error.message || error.error));
    
    // Store error for debugging
    pm.environment.set("lastError", JSON.stringify(error));
} else {
    console.log("Request successful");
}"""
        },
        
        "Multiple Assertions": {
            "description": "Run multiple test assertions",
            "code": """// Run multiple tests
const jsonData = pm.response.json();

pm.test("Status code is 200", function() {
    pm.expect(pm.response.code).to.equal(200);
});

pm.test("Response has data", function() {
    pm.expect(jsonData).to.have.property("data");
});

pm.test("Data is not empty", function() {
    pm.expect(jsonData.data).to.not.be.empty;
});

pm.test("Has success flag", function() {
    pm.expect(jsonData.success).to.be.true;
});

console.log("All tests executed");"""
        },
        
        "Save Response for Next Request": {
            "description": "Save response data for request chaining",
            "code": """// Save data for next request
const response = pm.response.json();

// Extract and save important IDs
if (response.id) {
    pm.environment.set("resourceId", response.id);
    console.log("Resource ID saved: " + response.id);
}

// Save entire response for reference
pm.collectionVariables.set("lastResponse", JSON.stringify(response));
console.log("Response data saved for chaining");"""
        },
        
        "Parse Text Response": {
            "description": "Handle non-JSON text responses",
            "code": """// Parse text response
const responseText = pm.response.text();

// Extract specific patterns from text
const match = responseText.match(/token=([a-zA-Z0-9]+)/);
if (match && match[1]) {
    pm.environment.set("authToken", match[1]);
    console.log("Token extracted from text: " + match[1]);
}

console.log("Response text length: " + responseText.length);"""
        }
    }
    
    @classmethod
    def get_pre_request_snippets(cls) -> Dict[str, Dict[str, str]]:
        """Get all pre-request script snippets."""
        return cls.PRE_REQUEST_SNIPPETS
    
    @classmethod
    def get_post_response_snippets(cls) -> Dict[str, Dict[str, str]]:
        """Get all post-response script snippets."""
        return cls.POST_RESPONSE_SNIPPETS
    
    @classmethod
    def get_snippet_names(cls, snippet_type: str = "pre_request") -> List[str]:
        """
        Get list of snippet names.
        
        Args:
            snippet_type: "pre_request" or "post_response"
        
        Returns:
            List of snippet names
        """
        if snippet_type == "pre_request":
            return list(cls.PRE_REQUEST_SNIPPETS.keys())
        elif snippet_type == "post_response":
            return list(cls.POST_RESPONSE_SNIPPETS.keys())
        else:
            return []
    
    @classmethod
    def get_snippet(cls, name: str, snippet_type: str = "pre_request") -> Dict[str, str]:
        """
        Get a specific snippet by name.
        
        Args:
            name: Snippet name
            snippet_type: "pre_request" or "post_response"
        
        Returns:
            Dictionary with 'description' and 'code' keys
        """
        if snippet_type == "pre_request":
            return cls.PRE_REQUEST_SNIPPETS.get(name, {"description": "", "code": ""})
        elif snippet_type == "post_response":
            return cls.POST_RESPONSE_SNIPPETS.get(name, {"description": "", "code": ""})
        else:
            return {"description": "", "code": ""}

