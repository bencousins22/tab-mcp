# Tabcorp API MCP Server

A Model Context Protocol (MCP) server for the Tabcorp betting API, built with [Smithery CLI](https://smithery.ai).

## Features

- **OAuth Authentication**: Password grant, refresh token, and client credentials flows
- **Tabcorp API Tools**: Query sports, competitions, markets, and place bets
- **Session Configuration**: Store credentials securely per-session
- **Auto-refresh**: Optional automatic token refresh when approaching expiry

## Prerequisites

- Python 3.10+
- Tabcorp API credentials (client_id, client_secret, username, password)
- Smithery API key (get yours at [smithery.ai/account/api-keys](https://smithery.ai/account/api-keys))

## Installation

```bash
# Clone and install
git clone <your-repo-url>
cd tab-mcp
uv sync
```

## Local Development

```bash
# Run in development mode
uv run dev

# Test interactively (requires Node.js)
uv run playground
```

## MCP Tools Available

### Authentication Tools

1. **tab_oauth_password_grant**: Obtain access and refresh tokens using password grant
   - Parameters: `client_id`, `client_secret`, `username`, `password`, `base_url` (all optional if set in config)
   - Returns: `access_token`, `refresh_token`, `expires_in`, `expires_at`

2. **tab_oauth_refresh**: Refresh access token using refresh_token
   - Parameters: `refresh_token`, `client_id`, `client_secret`, `base_url`
   - Returns: New `access_token`, `refresh_token`, `expires_in`, `expires_at`

3. **tab_oauth_client_credentials**: Get token for non-account queries
   - Parameters: `client_id`, `client_secret`, `base_url`
   - Returns: `access_token`, `expires_in`, `expires_at`

### API Query Tools

4. **tab_get**: Generic GET request with bearer token
   - Parameters: `access_token`, `path`, `params`, `jurisdiction`, `base_url`
   - Example: `path="/v1/tab-info-service/sports"`, `params={"jurisdiction": "NSW"}`

5. **tab_post**: Generic POST request with bearer token
   - Parameters: `access_token`, `path`, `body`, `base_url`
   - Use for placing bets or other POST operations

6. **tab_list_sports**: Convenience wrapper for listing sports
   - Parameters: `access_token`, `jurisdiction`, `base_url`
   - Returns: List of available sports and competitions

7. **hello**: Simple test tool
   - Parameters: `name`
   - Returns: Greeting message with jurisdiction from config

## Session Configuration

When connecting to this MCP server, you can provide session-level configuration:

```json
{
  "client_id": "your-tabcorp-client-id",
  "client_secret": "your-tabcorp-client-secret",
  "username": "your-tab-account-number",
  "password": "your-tab-password",
  "refresh_token": "optional-cached-refresh-token",
  "jurisdiction": "NSW",
  "base_url": "https://api.beta.tab.com.au",
  "auto_refresh": true
}
```

## Example Usage

### 1. Authenticate and Get Sports

```python
# First, get an access token using password grant
auth_result = tab_oauth_password_grant()
# Returns: {"access_token": "...", "refresh_token": "...", "expires_at": ...}

# Use the token to query sports
sports = tab_list_sports(access_token=auth_result["access_token"])
# Returns: {"sports": [{"id": "4", "name": "Basketball", ...}, ...]}
```

### 2. Refresh Token

```python
# When token is about to expire, refresh it
new_auth = tab_oauth_refresh(refresh_token=auth_result["refresh_token"])
# Returns: {"access_token": "...", "refresh_token": "...", "expires_at": ...}
```

### 3. Generic API Query

```python
# Query specific competition
competition = tab_get(
    access_token=auth_result["access_token"],
    path="/v1/tab-info-service/sports/Basketball/competitions/NBA",
    params={"jurisdiction": "NSW"}
)
```

## Deploy to Smithery

1. **Push to GitHub**:
   ```bash
   git add .
   git commit -m "Initial Tabcorp MCP server"
   git remote add origin https://github.com/YOUR_USERNAME/tab-mcp.git
   git push -u origin main
   ```

2. **Deploy on Smithery**:
   - Go to [smithery.ai/new](https://smithery.ai/new)
   - Connect your GitHub repository
   - Smithery will automatically detect the MCP server and deploy it
   - Configure secrets in Smithery dashboard if needed

3. **Use from MCP Clients**:
   - Once deployed, connect using Smithery's SDK or any MCP client
   - Provide session configuration with your Tabcorp credentials

## API Documentation

- [Tabcorp API Docs](https://api.beta.tab.com.au/)
- [OAuth 2.0 Flows](https://api.beta.tab.com.au/docs/authentication)
- [MCP Protocol](https://modelcontextprotocol.io)
- [Smithery Docs](https://smithery.ai/docs)

## Security Notes

- Never commit credentials to version control
- Use Smithery's secure configuration management for production
- Store refresh tokens securely and rotate regularly
- Enable auto_refresh to minimize token expiry issues

## License

MIT
