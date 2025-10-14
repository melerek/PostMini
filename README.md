# PostMini - Desktop API Client

**Version 1.1.2** | Professional API Testing Tool | MIT License

A simple and powerful desktop API client built with PyQt6. PostMini allows you to create, manage, and execute HTTP requests with full support for collections, environment variables, OAuth 2.0, API testing, code generation, dark mode, cURL import/export, and persistent storage.

![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)
![PyQt6](https://img.shields.io/badge/PyQt6-6.4%2B-green)
![Version](https://img.shields.io/badge/version-1.1.2-brightgreen)
![License](https://img.shields.io/badge/license-MIT-blue)
![Tests](https://img.shields.io/badge/tests-200%2B%20passing-success)

---

## 📖 Documentation

**[View Full Documentation (HTML)](docs/index.html)** - Open `docs/index.html` in your browser for comprehensive documentation with interactive navigation.

---

## 🆚 PostMini vs Postman

PostMini is a **free, open-source, privacy-focused** alternative to Postman:

| | PostMini | Postman Enterprise |
|---|:---:|:---:|
| **Price** | **FREE** | $49+/user/month |
| **Team Collaboration** | **Unlimited (Git)** | Unlimited (Cloud) |
| **Data Storage** | **100% Local** | Cloud |
| **Open Source** | **✅ MIT License** | ❌ Closed |
| **Git Integration** | **Native** | Limited |

💰 **Save $17,640** over 3 years for a 10-person team!

📊 **[See Full Comparison](docs/POSTMINI_VS_POSTMAN_COMPARISON.md)** | **[Quick Comparison](COMPARISON_QUICK.md)**

---

## Features

- **Collections Management**: Organize your API requests into collections
- **Environment Variables**: Use `{{variables}}` for reusable configurations across environments
- **Git-Based Collaboration**: 🌟 Version control collections with Git, enabling seamless team collaboration
- **Dark Mode**: 🆕 v1.1.2 - Beautiful dark theme with one-click toggle and persistence!
- **Application Icon**: 🆕 v1.1.2 - Professional branding in window and taskbar
- **cURL Import/Export**: 🆕 v1.1.2 - Paste cURL commands to create requests instantly!
- **Export/Import Collections**: Share collections with your team via JSON files
- **Request History**: Track, review, and replay all API requests
- **Code Generation**: Generate code in 7 languages (curl, Python, JS, Node, React, C#)
- **OAuth 2.0 Support**: Full OAuth 2.0 with Authorization Code, Client Credentials, and Password Grant flows
- **API Testing / Assertions**: 🌟 Automated testing with 8 assertion types, test runner, and results tracking
- **Multiple HTTP Methods**: Support for GET, POST, PUT, DELETE, PATCH, HEAD, and OPTIONS
- **Request Configuration**:
  - URL query parameters
  - Custom headers
  - Request body (JSON, text, etc.)
  - Bearer Token authentication
- **Response Viewer**:
  - Pretty-printed JSON responses
  - Response headers display
  - Status code, response time, and size information
- **Persistent Storage**: SQLite database for saving collections and requests
- **Modern UI**: Clean, intuitive three-pane interface with toolbar
- **Asynchronous Requests**: Non-blocking HTTP requests using threading

## Technology Stack

- **GUI Framework**: PyQt6
- **HTTP Client**: requests library
- **Database**: Python's built-in sqlite3 module

## Project Structure

The project follows a clean, modular architecture with clear separation of concerns:

```
PostMini/
├── main.py                    # Application entry point
├── requirements.txt           # Python dependencies  
├── styles.qss                 # Qt stylesheet
├── api_client.db              # SQLite database
│
├── src/                       # Source code
│   ├── core/                  # Core functionality (database, HTTP client)
│   ├── ui/                    # User interface
│   │   ├── dialogs/          # Dialog windows
│   │   └── widgets/          # Custom widgets
│   └── features/             # Feature modules (OAuth, testing, etc.)
│
├── tests/                    # Test suite
└── docs/                     # Documentation (includes index.html)
```

📖 **See [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) for detailed architecture documentation.**

## Installation

### For End Users (Windows Installer) 🆕

**The easiest way to get PostMini:**

1. Download `PostMini_Setup_v1.0.0.exe` from [Releases](https://github.com/yourusername/postmini/releases)
2. Run the installer and follow the wizard
3. Launch PostMini from Start Menu or Desktop shortcut

✅ **No Python installation required!**  
✅ **All dependencies bundled**  
✅ **Data safely stored in %APPDATA%\PostMini\**

See [INSTALLER_GUIDE.md](docs/INSTALLER_GUIDE.md) for complete installation documentation.

### For Developers (From Source)

#### Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

#### Setup

1. Clone or download this repository:
   ```bash
   cd PostMini
   ```

2. Create a virtual environment (recommended):
   ```bash
   # On Windows
   python -m venv venv
   venv\Scripts\activate

   # On macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. **(Optional) To build installer:**
   ```bash
   pip install -r requirements-dev.txt
   ```
   See [QUICK_BUILD_GUIDE.md](QUICK_BUILD_GUIDE.md) for building instructions.

## Usage

### Running the Application

```bash
python main.py
```

### Quick Start with Demo Data

Want to see environment variables in action? Run the demo script:

```bash
python demo_environments.py
python main.py
```

This will create sample environments (Development, Staging, Production) and requests that use variables like `{{baseUrl}}`, `{{apiKey}}`, etc.

### Getting Started

1. **Create an Environment** (Optional but Recommended):
   - Click "Manage Environments" in the toolbar
   - Click "Add" to create a new environment
   - Add variables like:
     - `baseUrl`: `https://jsonplaceholder.typicode.com`
     - `apiKey`: `your-api-key`
   - Click "Save Environment"
   - Select your environment from the dropdown in the toolbar

2. **Create a Collection**:
   - Click the "Add Collection" button in the left pane
   - Enter a name for your collection (e.g., "My API", "GitHub API")

3. **Add a Request**:
   - Select a collection in the tree
   - Click "Add Request"
   - Enter a name for the request (e.g., "Get Users", "Create Post")

4. **Configure the Request**:
   - Select the HTTP method from the dropdown (GET, POST, etc.)
   - Enter the URL (use variables like `{{baseUrl}}/users`)
   - **Params Tab**: Add query parameters as key-value pairs
   - **Headers Tab**: Add custom headers (e.g., `Authorization: Bearer {{apiToken}}`)
   - **Authorization Tab**: Select auth type and enter token (can use `{{token}}`)
   - **Body Tab**: Enter request body (can use variables in JSON)

5. **Send the Request**:
   - Click the "Send" button
   - Variables will be automatically substituted if an environment is selected
   - View the response in the bottom pane:
     - Status code, response time, and size
     - Response body (auto-formatted if JSON)
     - Response headers

6. **Save the Request**:
   - After configuring, click "Save" to persist changes to the database
   - Saved requests can be loaded by clicking on them in the tree

7. **Delete Items**:
   - Select a collection or request in the tree
   - Click "Delete" to remove it
   - Deleting a collection will also delete all its requests

## Database Schema

The application uses SQLite with the following schema:

### Collections Table
```sql
CREATE TABLE collections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
)
```

### Requests Table
```sql
CREATE TABLE requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    collection_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    method TEXT NOT NULL,
    url TEXT NOT NULL,
    params TEXT,
    headers TEXT,
    body TEXT,
    auth_type TEXT DEFAULT 'None',
    auth_token TEXT,
    FOREIGN KEY (collection_id) REFERENCES collections(id) ON DELETE CASCADE
)
```

### Environments Table
```sql
CREATE TABLE environments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    variables TEXT
)
```

## Example Usage

### Testing a REST API with Environment Variables

1. **Create an environment** named "JSONPlaceholder":
   - Variable: `baseUrl` = `https://jsonplaceholder.typicode.com`
   - Variable: `userId` = `1`
   - Select "JSONPlaceholder" from environment dropdown

2. **Create a collection** named "JSONPlaceholder API"

3. **Add a GET request**:
   - Name: "Get All Posts"
   - URL: `{{baseUrl}}/posts`
   - Click "Send"
   - View the JSON response

4. **Add a POST request**:
   - Name: "Create Post"
   - URL: `{{baseUrl}}/posts`
   - Method: POST
   - Headers Tab: Add `Content-Type: application/json`
   - Body Tab: 
     ```json
     {
       "title": "My New Post",
       "body": "This is the post content",
       "userId": {{userId}}
     }
     ```
   - Click "Send"
   - View the created resource in the response

### Using Environment Variables with Authentication

1. **Create environment variables**:
   - `apiUrl`: `https://api.example.com`
   - `authToken`: `your-bearer-token-here`

2. **Configure request**:
   - URL: `{{apiUrl}}/protected/resource`
   - Go to the "Authorization" tab
   - Select "Bearer Token" from the dropdown
   - Enter: `{{authToken}}`
   - The token will be automatically substituted and added as `Authorization: Bearer <actual-token>` header

### Testing Across Multiple Environments

1. **Create environments**:
   - Development: `baseUrl` = `https://dev-api.example.com`
   - Production: `baseUrl` = `https://api.example.com`

2. **Create request** with URL: `{{baseUrl}}/users`

3. **Switch environments**:
   - Select "Development" → Send → Tests against dev server
   - Select "Production" → Send → Tests against prod server

## Git-Based Collaboration

🌟 **NEW!** Version control your API collections with Git for seamless team collaboration! See **[GIT_SYNC_GUIDE.md](docs/GIT_SYNC_GUIDE.md)** for comprehensive documentation.

**Quick Overview:**
- Collections and environments sync to `.postmini/` folder
- Commit `.postmini/` to Git to share with your team
- Pull teammates' changes to auto-import their collections
- Secrets kept local and gitignored automatically
- Works with any Git hosting (GitHub, GitLab, Bitbucket)

**How It Works:**
1. Enable Git Sync in PostMini (click 🔄 Git Sync button)
2. Select your project directory
3. Collections auto-export to `.postmini/` folder on every save
4. **YOU commit to Git:** `git add .postmini/ && git commit -m "Update API collections" && git push`
5. Teammates run `git pull` and click "Import" in PostMini

**Important:** PostMini syncs to **files**, YOU commit files to **Git**!

**Use Cases:**
- 👥 Team collaboration on API collections
- 📝 PR reviews for API changes
- 🔄 Version control and history
- 🌿 Branch-based API development
- 🔐 Secure secrets management

## Environment Variables

The application includes a powerful environment variables system for team collaboration. See **[ENVIRONMENT_VARIABLES_GUIDE.md](docs/ENVIRONMENT_VARIABLES_GUIDE.md)** for comprehensive documentation.

**Quick Overview:**
- Use `{{variableName}}` syntax in URLs, headers, params, body, and auth tokens
- Create multiple environments (Dev, Staging, Prod)
- Switch between environments instantly
- Variables are automatically substituted when sending requests

**Example:**
```
URL: {{baseUrl}}/{{version}}/users
Headers: Authorization: Bearer {{apiToken}}

When environment "Development" is selected:
→ https://dev.api.example.com/v1/users
→ Authorization: Bearer dev-token-123
```

## Code Generation

Generate ready-to-use code snippets in 7 languages! See **[CODE_GENERATION_GUIDE.md](CODE_GENERATION_GUIDE.md)** for comprehensive documentation.

**Supported Languages:**
- ✅ curl (Command Line)
- ✅ Python (requests)
- ✅ JavaScript (fetch)
- ✅ JavaScript (axios)
- ✅ Node.js (https)
- ✅ React (Component)
- ✅ C# (HttpClient)

**How to Use:**
1. Configure your request (method, URL, params, headers, body, auth)
2. Click the **"💻 Code"** button (next to Save)
3. Select your language from the dropdown
4. Click **"📋 Copy to Clipboard"**
5. Paste into your application!

**Example:**
```bash
# Generated curl command
curl --request GET \
  --url 'https://api.example.com/users' \
  --header 'Authorization: Bearer token' \
  --header 'Content-Type: application/json'
```

**Use Cases:**
- 📋 Quick API integration
- 👥 Team documentation
- 📚 Learning different languages
- 🚀 Faster development

## OAuth 2.0 Authentication (NEW!)

Comprehensive OAuth 2.0 support for modern API authentication! See **[OAUTH_GUIDE.md](OAUTH_GUIDE.md)** for detailed documentation.

**Supported OAuth 2.0 Flows:**
- ✅ **Authorization Code Flow** (Recommended) - Opens browser for user authorization
- ✅ **Client Credentials Flow** - Server-to-server authentication
- ✅ **Password Grant Flow** - Legacy support for trusted applications

**How to Use:**
1. Go to **Authorization** tab and select **"OAuth 2.0"**
2. Click **"🔐 Configure OAuth"**
3. Add your OAuth configuration (client ID, secret, URLs)
4. Click **"🔐 Authorize"** to get an access token
5. Click **"✅ Use This Token"**
6. All requests now include your OAuth token automatically!

**Key Features:**
- 🔄 **Automatic Token Refresh** - Refresh expired tokens with one click
- 💾 **Secure Token Storage** - Tokens persist across sessions
- ⏰ **Expiry Checking** - Automatic validation before requests
- 🔐 **CSRF Protection** - State parameter validation
- 🌐 **Local Callback Server** - Handles OAuth redirects seamlessly

**Example: GitHub OAuth**
```
Authorization URL: https://github.com/login/oauth/authorize
Token URL: https://github.com/login/oauth/access_token
Scope: repo user
```

**Supported Providers:**
- GitHub, Google, Microsoft, Spotify, LinkedIn, and any OAuth 2.0 compliant API

**Use Cases:**
- 🔐 Authenticate with GitHub, Google, etc.
- 🤖 Access protected APIs
- 👥 User authorization workflows
- 🔄 Long-lived API access with token refresh

## Code Architecture

### database.py
Contains the `DatabaseManager` class that handles all SQLite operations:
- CRUD operations for collections
- CRUD operations for requests
- CRUD operations for environments
- JSON serialization/deserialization for complex fields

### api_client.py
Contains the `ApiClient` class for HTTP requests:
- Execute requests with various HTTP methods
- Handle authentication
- Return wrapped responses with metadata (time, size, etc.)
- Error handling for network issues

### main_window.py
Contains the `MainWindow` class with the complete UI:
- Three-pane layout (collections, request editor, response viewer)
- QTreeWidget for collections/requests hierarchy
- Toolbar with environment selector
- Request editor with tabs for params, headers, auth, and body
- Response viewer with pretty-printed JSON
- Threading for non-blocking HTTP requests
- Variable substitution integration

### environment_dialog.py
Contains the `EnvironmentDialog` class for managing environments:
- Create, edit, and delete environments
- Manage variables as key-value pairs
- User-friendly interface with list and editor views

### variable_substitution.py
Contains utility classes for variable substitution:
- `VariableSubstitution`: Pattern matching and replacement for `{{variables}}`
- `EnvironmentManager`: Manages active environment and variable resolution
- Supports substitution in URLs, headers, params, body, and auth tokens

### code_generator.py
Contains the `CodeGenerator` class for generating code snippets:
- 7 language generators (curl, Python, JavaScript, Node.js, React, C#)
- Smart formatting and pretty-printing
- Handles params, headers, body, and authentication
- Special character escaping for shell safety

### code_snippet_dialog.py
Contains the `CodeSnippetDialog` class for viewing generated code:
- Language selector with real-time code updates
- Monospace font for code readability
- One-click clipboard copy
- Clean, professional UI

### history_dialog.py
Contains the `HistoryDialog` class for viewing request history:
- Displays all executed requests with timestamps
- Shows response status, time, and size
- Replay functionality to load past requests
- Clear history options

### collection_io.py
Contains classes for collection import/export:
- `CollectionExporter`: Serialize collections to JSON
- `CollectionImporter`: Deserialize and import collections
- Handles duplicate collection names
- Validation and error handling

### oauth_manager.py
Contains the `OAuthManager` class for OAuth 2.0 flows:
- Authorization Code Flow implementation
- Client Credentials Flow implementation
- Password Grant Flow implementation
- Token refresh logic
- Local HTTP callback server for OAuth redirects
- Token expiry management and utilities
- CSRF protection with state parameter

### oauth_dialog.py
Contains the `OAuthConfigDialog` class for OAuth management:
- Two-tab interface (Manage Configs, Add/Edit Config)
- OAuth configuration CRUD operations
- Authorization flow execution with progress dialog
- Token status display and management
- Refresh and clear token functionality
- Integration with OAuth Manager and Database

### main.py
Application entry point that initializes and runs the Qt application.

### demo_environments.py
Demo script that creates sample data to showcase environment variables feature.

## Error Handling

The application includes comprehensive error handling for:
- Network connection errors
- Request timeouts
- Invalid URLs
- JSON parsing errors
- Database constraints (e.g., duplicate collection names)
- Invalid JSON in request body

All errors are displayed to the user via message boxes or in the response viewer.

## Development

### Running in Development Mode

```bash
python main.py
```

### Adding New Features

The modular architecture makes it easy to extend:
- Add new authentication types in `api_client.py`
- Add new request configuration options in `main_window.py`
- Extend database schema in `database.py`

## Troubleshooting

### Issue: Application won't start
- Ensure Python 3.8+ is installed: `python --version`
- Verify all dependencies are installed: `pip install -r requirements.txt`
- Check for error messages in the console

### Issue: Database errors
- Delete `api_client.db` file and restart the application to recreate the database
- Ensure you have write permissions in the application directory

### Issue: Network/SSL errors
- Check your internet connection
- Some APIs may require specific headers or authentication
- Try with a simple API first (e.g., https://jsonplaceholder.typicode.com)

## Contributing

Contributions are welcome! Feel free to:
- Report bugs
- Suggest new features
- Submit pull requests

## License

This project is licensed under the MIT License.

## Acknowledgments

- Built with PyQt6 for the GUI framework
- Uses the requests library for HTTP operations
- Inspired by Postman and other professional API client tools
- PostMini - A simple yet powerful alternative for desktop API testing

## Contact

For questions or support, please open an issue in the repository.

---

**Happy API Testing! 🚀**

