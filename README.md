# Tabcorp API MCP Server

Comprehensive Model Context Protocol (MCP) server for the Tabcorp betting API with full endpoint coverage.

## Features

### OAuth Authentication (3 tools)
- Password grant (personal account betting)
- Refresh token flow
- Client credentials (public data access)

### Racing Endpoints (11 tools)
- Get all meeting dates
- Get meetings for a date
- Get races in a meeting
- Get race details
- Get next-to-go races
- Get race form guides
- Get runner form
- Get pool approximates
- Get jackpot pools
- Get open jackpots

### Sports Endpoints (8 tools)
- Get all open sports
- Get open sport details
- Get open competitions
- Get open tournaments
- Get open matches (in competitions and tournaments)
- Get next-to-go matches

### Sports Results (4 tools)
- Get all resulted sports
- Get resulted competitions
- Get resulted matches
- Get resulted tournaments

### FootyTAB (2 tools)
- Get all rounds
- Get round details

### Generic API Tools (2 tools)
- Generic GET requests
- Generic POST requests

**Total: 30+ specialized Tabcorp API tools**

## Prerequisites

- Python 3.10+
- Tabcorp API credentials
- Smithery API key: [smithery.ai/account/api-keys](https://smithery.ai/account/api-keys)

## Installation

```bash
git clone https://github.com/bencousins22/tab-mcp.git
cd tab-mcp
uv sync
```

## Local Development

```bash
uv run dev  # Starts server on port 8081
```

## Session Configuration

Provide these when connecting to the MCP server:

```json
{
  "client_id": "your-tabcorp-client-id",
  "client_secret": "your-tabcorp-client-secret",
  "username": "your-tab-account-number",
  "password": "your-tab-password",
  "jurisdiction": "NSW",
  "base_url": "https://api.beta.tab.com.au"
}
```

## Example Usage

### 1. Authenticate
```javascript
const auth = await tab_oauth_password_grant();
// Returns: { access_token, refresh_token, expires_at, ... }
```

### 2. Get Racing Meetings Today
```javascript
const dates = await racing_get_all_meeting_dates({
  access_token: auth.access_token,
  jurisdiction: "NSW"
});

const meetings = await racing_get_meetings({
  access_token: auth.access_token,
  meeting_date: "2025-10-29",
  jurisdiction: "NSW"
});
```

### 3. Get Next-to-Go Races
```javascript
const nextRaces = await racing_get_next_to_go({
  access_token: auth.access_token,
  max_races: 10
});
```

### 4. Get Sports
```javascript
const sports = await sports_get_all_open({
  access_token: auth.access_token,
  jurisdiction: "NSW"
});

const nba = await sports_get_open_competition({
  access_token: auth.access_token,
  sport_name: "Basketball",
  competition_name: "NBA"
});
```

### 5. Get FootyTAB Rounds
```javascript
const rounds = await footytab_get_all_rounds({
  access_token: auth.access_token,
  sport_name: "AFL",
  jurisdiction: "VIC"
});
```

## Deploy to Smithery

1. **Push to GitHub** (already done)
2. **Deploy**: Visit [smithery.ai/new](https://smithery.ai/new)
3. **Connect**: Select `bencousins22/tab-mcp`
4. **Configure Secrets**:
   - `TAB_CLIENT_ID`
   - `TAB_CLIENT_SECRET`
   - `TAB_USERNAME` (optional)
   - `TAB_PASSWORD` (optional)

## API Endpoints Reference

### Racing
- `racing_get_all_meeting_dates` - All available dates
- `racing_get_meetings` - Meetings for a date
- `racing_get_all_races_in_meeting` - All races in meeting
- `racing_get_race` - Single race details
- `racing_get_next_to_go` - Next races by time
- `racing_get_race_form` - Race form guide
- `racing_get_runner_form` - Runner form guide
- `racing_get_approximates` - Pool approximates
- `racing_get_jackpot_pools` - Jackpots for date
- `racing_get_open_jackpots` - All open jackpots

### Sports
- `sports_get_all_open` - All open sports
- `sports_get_open_sport` - Specific sport
- `sports_get_open_competition` - Specific competition
- `sports_get_open_tournament` - Specific tournament
- `sports_get_open_match_in_competition` - Match in competition
- `sports_get_open_match_in_tournament` - Match in tournament
- `sports_get_next_to_go` - Next matches by time

### Sports Results
- `sports_get_all_results` - All resulted sports
- `sports_get_resulted_sport` - Resulted sport
- `sports_get_resulted_competition` - Resulted competition
- `sports_get_resulted_match_in_competition` - Match results

### FootyTAB
- `footytab_get_all_rounds` - All rounds for sport
- `footytab_get_round_details` - Specific round details

### Generic
- `tab_get` - Any GET endpoint
- `tab_post` - Any POST endpoint

## Supported Jurisdictions

- `NSW` - New South Wales
- `VIC` - Victoria
- `QLD` - Queensland
- `SA` - South Australia
- `TAS` - Tasmania
- `ACT` - Australian Capital Territory
- `NT` - Northern Territory

## Race Types

- `R` - Thoroughbred Racing
- `H` - Harness Racing
- `G` - Greyhound Racing

## Resources

- **Repository**: https://github.com/bencousins22/tab-mcp
- **Tabcorp API**: https://api.beta.tab.com.au/
- **MCP Protocol**: https://modelcontextprotocol.io
- **Smithery**: https://smithery.ai

## License

MIT
