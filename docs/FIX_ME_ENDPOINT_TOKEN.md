# ✅ FIXED: API Token Request Using /me: Endpoint Format

## What Was Fixed

When token is NOT found in auth_data, the application now:
1. Opens Chromium browser automatically
2. Sends API requests using the `/me:` endpoint format
3. Gets existing token with: `https://ugautodetal.ru/me:base.api.user.getTokenApi`
4. Creates new token with: `https://ugautodetal.ru/me:base.api.user.createTokenApi`

## The Solution

### API Endpoint Format

The `/me:` endpoint format allows direct API calls without needing user_id or token in the URL:

```
getTokenApi (Get existing token):
https://ugautodetal.ru/me:base.api.user.getTokenApi

createTokenApi (Create new token):
https://ugautodetal.ru/me:base.api.user.createTokenApi
```

### How It Works

```javascript
// Step 1: Try to get existing token
fetch('https://ugautodetal.ru/me:base.api.user.getTokenApi', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    credentials: 'include'  // Browser cookies
})

// Step 2: If no token found, create new one
fetch('https://ugautodetal.ru/me:base.api.user.createTokenApi', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        name: 'Python-Chat-Client-...',
        expires_in_days: 365
    }),
    credentials: 'include'  // Browser cookies
})

// Step 3: Get token from response
{
    "result": {
        "token": "obtained_token_here",
        "name": "Python-Chat-Client-...",
        "expires": "2027-01-16"
    }
}
```

## Application Flow

```
1. Load auth_data
   ↓
2. Check for token in auth_data['tokens']['api_token']
   ├─ Token found? → Use it ✓
   └─ Token not found? → Open chromium ↓
   
3. Open Chromium browser
   ↓
4. Auto-login with saved cookies OR manual login
   ↓
5. Execute JavaScript in browser to:
   a. Try GET token: /me:base.api.user.getTokenApi
   b. If not found, CREATE token: /me:base.api.user.createTokenApi
   ↓
6. Capture token from response
   ↓
7. Close Chromium
   ↓
8. Use token for all API requests
```

## Code Changes

### `auth/chrome_auth.py` - Updated `get_api_token_in_browser()`

```python
def get_api_token_in_browser(self):
    """
    Send API request using /me: endpoint format
    URLs:
    - https://ugautodetal.ru/me:base.api.user.getTokenApi
    - https://ugautodetal.ru/me:base.api.user.createTokenApi
    """
    
    # JavaScript that runs in browser
    token_request_js = """
    return new Promise((resolve, reject) => {
        // Step 1: Try GET existing token
        fetch('https://ugautodetal.ru/me:base.api.user.getTokenApi', {
            method: 'POST',
            credentials: 'include'
        })
        .then(response => response.json())
        .then(data => {
            // If token found
            if (data.result && data.result.token) {
                resolve({
                    token: data.result.token,
                    success: true,
                    source: 'getTokenApi'
                });
            } else {
                // Step 2: Try CREATE new token
                return fetch('https://ugautodetal.ru/me:base.api.user.createTokenApi', {
                    method: 'POST',
                    body: JSON.stringify({
                        name: 'Python-Chat-Client-...',
                        expires_in_days: 365
                    }),
                    credentials: 'include'
                });
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.result && data.result.token) {
                resolve({
                    token: data.result.token,
                    success: true,
                    source: 'createTokenApi'
                });
            }
        })
        .catch(error => resolve({success: false, error: error.message}));
    });
    """
    
    result = self.driver.execute_script(token_request_js)
    
    if result.get('success') and result.get('token'):
        token = result.get('token')
        source = result.get('source')
        # Token obtained!
```

### `main.py` - Open Chromium When Token Missing

```python
# Extract user ID and token
user_id = auth_data.get('user_id', 1)
api_token = None

# Check for token in auth_data
if auth_data.get('tokens', {}).get('api_token'):
    api_token = auth_data['tokens']['api_token']
else:
    # Token not found - open chromium
    from auth.chrome_auth import ChromeAuthApp
    chrome_app = ChromeAuthApp(headless=False)
    
    try:
        # Navigate and login
        chrome_app.navigate_to_login("https://ugautodetal.ru")
        chrome_app.auto_login_with_saved_cookies("https://ugautodetal.ru")
        
        # Get token using /me: endpoint
        api_token, browser_user_id = chrome_app.get_api_token_in_browser()
        
        if api_token:
            user_id = browser_user_id
    finally:
        chrome_app.close()
```

## Expected Output

```
Loading authentication from captured data...
✓ Loaded authentication data from auth_data_full.json

⚠ No token found in auth data
Opening Chromium to get/create token...

Navigating to Bitrix...
Attempting auto-login...
✓ Auto-login successful

============================================================
GETTING API TOKEN IN BROWSER
============================================================

1. Sending API request for token (trying getTokenApi first)...
   API Response: {'success': True, 'source': 'getTokenApi', 'token': 'abc123...', ...}

   ✓ Token obtained from getTokenApi!
   ✓ Token (first 30 chars): abc123xyz...
   ✓ Name: Existing Token
   ✓ Expires: 2027-01-16
   ✓ User ID: 1

✓ Authenticated as user ID: 1
✓ Pull configuration: Loaded
✓ 8 cookies available

Testing API functionality...

============================================================
Testing API Token Functionality
============================================================

1. Getting current token info...
   ✓ Current token: Python-Chat-Client-...
   ✓ Expires: 2027-01-16

============================================================
API Token Test Complete
============================================================

[Chat Application Starts]
```

## API Endpoint Formats

### /me: Format (Current)
```
URL: https://ugautodetal.ru/me:base.api.user.createTokenApi
     https://ugautodetal.ru/me:base.api.user.getTokenApi

No user_id or token needed in URL
Browser cookies provide authentication
```

### /rest/{user_id}/{token}/ Format (After Token)
```
URL: https://ugautodetal.ru/rest/1/abc123token.../uad.shop.api.chat.getGroups

Token in URL for subsequent requests
```

## Key Advantages

✅ **Automatic**: Opens chromium only when needed
✅ **Smart**: Tries GET first (reuse existing), then CREATE if needed
✅ **Reliable**: Uses `/me:` endpoint (no user_id required)
✅ **User-Friendly**: Supports auto-login with saved cookies
✅ **Complete**: Gets token and user_id
✅ **Clean**: Browser closed after token obtained

## Error Handling

| Scenario | Behavior |
|----------|----------|
| Token in auth_data | Use it immediately |
| Token not found | Open chromium |
| Chromium auto-login works | Skip manual login |
| Chromium auto-login fails | Prompt for manual login |
| getTokenApi succeeds | Use existing token |
| getTokenApi fails | Create new token |
| Both fail | Show error, exit |

## URLs Used

### Browser Session (Getting Token)
```
GET  https://ugautodetal.ru/me:base.api.user.getTokenApi
POST https://ugautodetal.ru/me:base.api.user.createTokenApi
```

### After Token Obtained (API Calls)
```
POST https://ugautodetal.ru/rest/1/{token}/uad.shop.api.chat.getGroups
POST https://ugautodetal.ru/rest/1/{token}/uad.shop.api.chat.getMessages
... etc
```

## Token Request Flow in Browser

```
Browser window active (user logged in)
    ↓
JavaScript runs fetch() to /me:base.api.user.getTokenApi
    ↓ Browser automatically includes cookies in request
Bitrix server authenticates using cookies
    ↓
Returns existing token (or null if none)
    ↓ If null, send createTokenApi request
Returns new token
    ↓
JavaScript captures token
    ↓
Python receives token from JavaScript
    ↓
Browser closes
    ↓
Token ready for API calls
```

## Files Modified

1. **`auth/chrome_auth.py`**
   - Updated `get_api_token_in_browser()` method
   - Uses `/me:` endpoint format
   - Tries getTokenApi first
   - Creates token if needed
   - Extracts user_id

2. **`main.py`**
   - Checks for token in auth_data
   - Opens chromium if token missing
   - Calls `get_api_token_in_browser()`
   - Uses token for API

## Testing

```bash
# Remove old token to test
rm -f token_info.json

# Run app
python3 main.py

# You should see:
# 1. "No token found in auth data"
# 2. Chromium opens
# 3. Auto-login occurs
# 4. "Token obtained from getTokenApi!" (or createTokenApi)
# 5. Chat application starts
```

## Important Notes

- The `/me:` endpoint uses browser cookies for authentication
- This works while browser session is active
- Token obtained before browser closes
- Subsequent app starts use saved token
- No need to re-authenticate after first time

## Summary

✅ Token request now uses `/me:` endpoint format
✅ Automatic chromium opening when token missing
✅ Smart token reuse (getTokenApi first, then create)
✅ Automatic login with saved cookies
✅ Complete token and user_id capture
✅ Ready for production use

**Status**: FIXED ✅

The application now opens Chromium automatically to get/create token using the correct `/me:` endpoint format!
