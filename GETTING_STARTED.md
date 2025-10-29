# Getting Started with Tabcorp MCP Server

## Welcome! 🎉

This guide will help you get started with the Tabcorp MCP Server - a comprehensive Model Context Protocol (MCP) server providing access to Tabcorp's betting API with 28 specialized tools.

**What you'll learn:**
- Setting up your development environment
- Obtaining Tabcorp API credentials
- Making your first API call
- Understanding authentication flows
- Using racing and sports betting tools
- Best practices and common patterns

---

## Prerequisites

### Required
- **Python 3.10+** installed on your system
- **Tabcorp account** (for betting features) OR **Developer credentials** (for public data)
- **Basic Python knowledge**
- **Internet connection**

### Recommended
- **Git** for version control
- **Code editor** (VS Code, PyCharm, etc.)
- **Terminal/command line** familiarity

---

## Step 1: Installation

### Option A: Using the Live Server (Easiest)

No installation required! Use our hosted server:

**Server URL**: `https://server.smithery.ai/@bencousins22/tab-mcp/mcp`

Connect directly via MCP client or API calls.

### Option B: Local Development Setup

**Clone the repository:**
```bash
git clone https://github.com/bencousins22/tab-mcp.git
cd tab-mcp
```

**Install dependencies:**
```bash
# Using uv (recommended)
uv sync

# Or using pip
pip install -r requirements.txt
```

**Install the package in editable mode:**
```bash
pip install -e .
```

---

## Step 2: Get API Credentials

### For Personal Betting (Password Grant)

You'll need:
1. **TAB Account Number** - Your existing Tabcorp account
2. **TAB Password** - Your account password  
3. **OAuth Client ID** - Request from Tabcorp developer portal
4. **OAuth Client Secret** - Provided with client ID

**How to obtain:**
- Visit Tabcorp Developer Portal (contact Tabcorp support)
- Register your application
- Request OAuth credentials
- Link credentials to your TAB account

### For Public Data Only (Client Credentials)

You'll need:
1. **OAuth Client ID**
2. **OAuth Client Secret**

**Note**: Client credentials grant only provides access to public racing/sports data. Cannot place bets or access account information.

---

## Step 3: Configure Environment

### Create Environment File

Copy the example environment file:
```bash
cp .env.example .env
```

### Edit Configuration

Open `.env` and add your credentials:

```bash
# OAuth Credentials
TAB_CLIENT_ID=your_client_id_here
TAB_CLIENT_SECRET=your_client_secret_here

# Personal Account (for betting)
TAB_USERNAME=your_tab_account_number
TAB_PASSWORD=your_tab_password

# Default Settings
DEFAULT_JURISDICTION=NSW
TAB_BASE_URL=https://api.beta.tab.com.au
```

**Security Note**: 
- Never commit `.env` to version control
- Keep credentials secure and private
- Rotate credentials every 90 days
- Enable 2FA on your TAB account

---

## Step 4: Start the Server (Local Development)

### Development Mode

```bash
# Run development server
uv run dev

# Server starts on http://localhost:8081
```

### Production Mode

```bash
# Run production server
uv run start
```

### Verify Server is Running

Open browser to `http://localhost:8081` - you should see the MCP server interface.

---

## Step 5: Your First API Call

### Using Python (Recommended for Beginners)

Create a file `test_connection.py`:

```python
import asyncio
import os
from dotenv import load_dotenv
from mcp.client import Client

load_dotenv()

async def test_connection():
    """Test connection to Tabcorp MCP Server"""

    # Connect to server
    async with Client("http://localhost:8081") as client:

        # 1. Authenticate using client credentials
        auth_result = await client.call_tool(
            "tab_oauth_client_credentials",
            {
                "client_id": os.getenv("TAB_CLIENT_ID"),
                "client_secret": os.getenv("TAB_CLIENT_SECRET")
            }
        )

        print("✅ Authentication successful!")
        access_token = auth_result["access_token"]
        print(f"Access Token: {access_token[:20]}...")

        # 2. Get next-to-go races
        races_result = await client.call_tool(
            "racing_get_next_to_go",
            {
                "access_token": access_token,
                "count": 3
            }
        )

        print("
📅 Next-to-Go Races:")
        for race in races_result["races"]:
            print(f"  - {race['meeting_name']} Race {race['race_number']}")
            print(f"    Starts in: {race['minutes_to_start']} minutes")

if __name__ == "__main__":
    asyncio.run(test_connection())
```

Run the test:
```bash
python test_connection.py
```

**Expected Output:**
```
✅ Authentication successful!
Access Token: eyJhbGciOiJSUzI1Ni...

📅 Next-to-Go Races:
- Randwick Race 3
  Starts in: 5 minutes
- Flemington Race 4
  Starts in: 12 minutes
- Eagle Farm Race 2
  Starts in: 18 minutes
```

---

## Step 6: Explore Available Tools

### List All Tools

```python
async def list_tools():
    async with Client("http://localhost:8081") as client:
        tools = await client.list_tools()

        print("Available Tools:")
        for tool in tools:
            print(f"  - {tool.name}: {tool.description}")

asyncio.run(list_tools())
```

### Tool Categories

1. **OAuth Authentication** (3 tools)
   - `tab_oauth_password_grant`
   - `tab_oauth_refresh`
   - `tab_oauth_client_credentials`

2. **Racing API** (10 tools)
   - `racing_get_all_meeting_dates`
   - `racing_get_meetings`
   - `racing_get_all_races_in_meeting`
   - `racing_get_race`
   - `racing_get_next_to_go`
   - `racing_get_race_form`
   - `racing_get_runner_form`
   - `racing_get_approximates`
   - `racing_get_open_jackpots`
   - `racing_get_jackpot_pools`

3. **Sports API** (7 tools)
   - `sports_get_all_open`
   - `sports_get_open_sport`
   - `sports_get_open_competition`
   - `sports_get_open_tournament`
   - `sports_get_open_match_in_competition`
   - `sports_get_open_match_in_tournament`
   - `sports_get_next_to_go`

4. **Sports Results** (4 tools)
   - `sports_get_all_results`
   - `sports_get_resulted_sport`
   - `sports_get_resulted_competition`
   - `sports_get_resulted_match_in_competition`

5. **FootyTAB** (2 tools)
   - `footytab_get_all_rounds`
   - `footytab_get_round_details`

6. **Generic API** (2 tools)
   - `tab_get`
   - `tab_post`

For detailed documentation of each tool, see [API_REFERENCE.md](API_REFERENCE.md).

---

## Step 7: Common Use Cases

### Use Case 1: Check Upcoming Races

```python
async def check_upcoming_races():
    async with Client("http://localhost:8081") as client:
        # Authenticate
        auth = await client.call_tool(
            "tab_oauth_client_credentials",
            {"client_id": CLIENT_ID, "client_secret": CLIENT_SECRET}
        )
        token = auth["access_token"]

        # Get next 5 races
        races = await client.call_tool(
            "racing_get_next_to_go",
            {"access_token": token, "count": 5}
        )

        return races["races"]
```

### Use Case 2: Get Race Form Guide

```python
async def get_form_guide(meeting_id, race_number):
    async with Client("http://localhost:8081") as client:
        auth = await client.call_tool("tab_oauth_client_credentials", {...})
        token = auth["access_token"]

        # Get detailed form
        form = await client.call_tool(
            "racing_get_race_form",
            {
                "access_token": token,
                "meeting_id": meeting_id,
                "race_number": race_number
            }
        )

        return form
```

### Use Case 3: Find Soccer Matches

```python
async def find_soccer_matches():
    async with Client("http://localhost:8081") as client:
        auth = await client.call_tool("tab_oauth_client_credentials", {...})
        token = auth["access_token"]

        # Get all open soccer competitions
        soccer = await client.call_tool(
            "sports_get_open_sport",
            {"access_token": token, "sport_id": "FOOT"}
        )

        # Get EPL matches
        epl = await client.call_tool(
            "sports_get_open_competition",
            {
                "access_token": token,
                "sport_id": "FOOT",
                "competition_id": "EPL"
            }
        )

        return epl["matches"]
```

---

## Step 8: Error Handling

### Always Use Try-Except

```python
from tab_mcp.server import TabcorpAPIError

async def safe_api_call():
    try:
        async with Client("http://localhost:8081") as client:
            result = await client.call_tool(
                "racing_get_next_to_go",
                {"access_token": token, "count": 5}
            )
            return result

    except TabcorpAPIError as e:
        print(f"API Error: {e.message}")
        print(f"Status Code: {e.status_code}")

        # Handle specific errors
        if e.status_code == 401:
            print("Token expired - re-authenticate")
        elif e.status_code == 429:
            print("Rate limited - wait before retry")

    except Exception as e:
        print(f"Unexpected error: {e}")
```

---

## Step 9: Best Practices

### 1. Token Management

```python
class TokenManager:
    def __init__(self):
        self.token = None
        self.expires_at = 0

    async def get_token(self, client):
        import time

        # Check if token is still valid
        if self.token and time.time() < self.expires_at:
            return self.token

        # Get new token
        auth = await client.call_tool(
            "tab_oauth_client_credentials",
            {"client_id": CLIENT_ID, "client_secret": CLIENT_SECRET}
        )

        self.token = auth["access_token"]
        self.expires_at = auth["expires_at"]

        return self.token
```

### 2. Rate Limiting

```python
import asyncio
from datetime import datetime, timedelta

class RateLimiter:
    def __init__(self, max_calls=10, period=60):
        self.max_calls = max_calls
        self.period = period
        self.calls = []

    async def wait_if_needed(self):
        now = datetime.now()
        # Remove old calls
        self.calls = [c for c in self.calls if now - c < timedelta(seconds=self.period)]

        if len(self.calls) >= self.max_calls:
            sleep_time = (self.calls[0] + timedelta(seconds=self.period) - now).total_seconds()
            await asyncio.sleep(sleep_time)

        self.calls.append(now)
```

### 3. Caching Results

```python
import json
import hashlib
from datetime import datetime, timedelta

class SimpleCache:
    def __init__(self, ttl=300):  # 5 minutes default
        self.cache = {}
        self.ttl = ttl

    def get(self, key):
        if key in self.cache:
            data, timestamp = self.cache[key]
            if datetime.now() - timestamp < timedelta(seconds=self.ttl):
                return data
        return None

    def set(self, key, value):
        self.cache[key] = (value, datetime.now())

    @staticmethod
    def make_key(*args, **kwargs):
        key_str = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()
```

---

## Step 10: Next Steps

### Learn More

📚 **Documentation**:
- [API Reference](API_REFERENCE.md) - Complete tool documentation
- [Tutorial: Building a Betting Bot](TUTORIAL_BETTING_BOT.md)
- [Tutorial: Racing Form Analysis](TUTORIAL_FORM_ANALYSIS.md)
- [Tutorial: Sports Odds Comparison](TUTORIAL_ODDS_COMPARISON.md)

🔧 **Advanced Topics**:
- [Deployment Guide](DEPLOYMENT.md) - Production deployment
- [Security Best Practices](SECURITY.md) - Credential management
- [Testing Guide](TESTING_SUMMARY.md) - Running tests

💡 **Examples**:
- Browse `examples/` directory for sample applications
- Check GitHub issues for community solutions

### Join the Community

- **GitHub**: https://github.com/bencousins22/tab-mcp
- **Issues**: Report bugs or request features
- **Discussions**: Ask questions and share ideas

---

## Troubleshooting

### Common Issues

#### "Authentication failed"
✅ **Solution**: 
- Verify credentials in `.env` file
- Check client ID and secret are correct
- Ensure account is active

#### "Connection refused"
✅ **Solution**:
- Verify server is running (`uv run dev`)
- Check port 8081 is not in use
- Firewall may be blocking connection

#### "Rate limit exceeded"
✅ **Solution**:
- Implement rate limiting in your code
- Add delays between requests
- Cache frequently accessed data

#### "Invalid jurisdiction"
✅ **Solution**:
- Use valid jurisdictions: NSW, VIC, QLD, SA, TAS, ACT, NT
- Check spelling and capitalization

#### "Token expired"
✅ **Solution**:
- Tokens expire after 1 hour
- Use refresh token to get new access token
- Implement automatic token refresh

### Getting Help

1. Check this guide and API reference first
2. Search GitHub issues for similar problems
3. Review error messages carefully
4. Enable debug logging for more details
5. Open a GitHub issue with:
   - Clear description of problem
   - Steps to reproduce
   - Error messages
   - Your environment (Python version, OS)

---

## Summary

Congratulations! You've completed the Getting Started guide. You should now be able to:

✅ Install and configure the Tabcorp MCP Server  
✅ Obtain and configure API credentials  
✅ Make authenticated API calls  
✅ Use racing and sports betting tools  
✅ Handle errors gracefully  
✅ Follow best practices  

**Ready to build something amazing?** Check out our tutorials for complete project examples!

---

**Need Help?** Open an issue on [GitHub](https://github.com/bencousins22/tab-mcp/issues)

**Last Updated**: October 29, 2024  
**Version**: 1.0.0
