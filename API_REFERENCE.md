# Tabcorp MCP Server - API Reference

## Overview

This document provides comprehensive API reference documentation for all 28 tools available in the Tabcorp MCP Server.

**Server URL**: https://server.smithery.ai/@bencousins22/tab-mcp/mcp  
**Base API**: https://api.beta.tab.com.au  
**Protocol**: Model Context Protocol (MCP) v1.0  
**Repository**: https://github.com/bencousins22/tab-mcp

---

## Table of Contents

1. [OAuth Authentication Tools](#oauth-authentication-tools) (3 tools)
2. [Racing API Tools](#racing-api-tools) (10 tools)
3. [Sports API Tools](#sports-api-tools) (7 tools)
4. [Sports Results Tools](#sports-results-tools) (4 tools)
5. [FootyTAB Tools](#footytab-tools) (2 tools)
6. [Generic API Tools](#generic-api-tools) (2 tools)
7. [Common Patterns](#common-patterns)
8. [Error Handling](#error-handling)

---

## OAuth Authentication Tools

Authentication tools for obtaining and managing access tokens required by all other API endpoints.

### 1. tab_oauth_password_grant

Obtain access token using password grant (account-based betting).

**Use Case**: Personal account betting, requires TAB account credentials.

**Parameters**:
- `client_id` (Optional[str]): OAuth client ID. Falls back to session config if not provided.
- `client_secret` (Optional[str]): OAuth client secret. Falls back to session config if not provided.
- `username` (Optional[str]): TAB account number. Falls back to session config if not provided.
- `password` (Optional[str]): TAB account password. Falls back to session config if not provided.

**Returns**:
```json
{
  "access_token": "eyJhbGciOiJSUzI1Ni...",
  "token_type": "Bearer",
  "expires_in": 3600,
  "expires_at": 1698765432,
  "refresh_token": "def502000a1b2c3d...",
  "scope": "betting"
}
```

**Example Usage**:
```python
# Using session config
result = await tab_oauth_password_grant(ctx)

# Explicit credentials
result = await tab_oauth_password_grant(
    ctx,
    client_id="your_client_id",
    client_secret="your_client_secret",
    username="your_tab_account",
    password="your_password"
)
```

**Errors**:
- `TabcorpAPIError`: Invalid credentials, network errors, timeout
- Status 401: Authentication failed
- Status 400: Invalid request parameters

---

### 2. tab_oauth_refresh

Refresh an expired access token using a refresh token.

**Use Case**: Extend session without re-entering credentials.

**Parameters**:
- `refresh_token` (Optional[str]): Refresh token from previous auth. Falls back to session config.
- `client_id` (Optional[str]): OAuth client ID. Falls back to session config.
- `client_secret` (Optional[str]): OAuth client secret. Falls back to session config.

**Returns**:
```json
{
  "access_token": "eyJhbGciOiJSUzI1Ni...",
  "token_type": "Bearer",
  "expires_in": 3600,
  "expires_at": 1698765432,
  "refresh_token": "def502000a1b2c3d...",
  "scope": "betting"
}
```

**Example Usage**:
```python
# Using cached refresh token from session
result = await tab_oauth_refresh(ctx)

# Explicit refresh token
result = await tab_oauth_refresh(
    ctx,
    refresh_token="def502000a1b2c3d...",
    client_id="your_client_id",
    client_secret="your_client_secret"
)
```

**Best Practices**:
- Tokens expire after 3600 seconds (1 hour)
- System auto-calculates `expires_at` with 60s buffer
- Refresh before expiry to maintain continuous access

---

### 3. tab_oauth_client_credentials

Obtain access token using client credentials (public data access only).

**Use Case**: Read-only access to public racing/sports data without account.

**Parameters**:
- `client_id` (Optional[str]): OAuth client ID. Falls back to session config.
- `client_secret` (Optional[str]): OAuth client secret. Falls back to session config.

**Returns**:
```json
{
  "access_token": "eyJhbGciOiJSUzI1Ni...",
  "token_type": "Bearer",
  "expires_in": 3600,
  "expires_at": 1698765432,
  "scope": "public"
}
```

**Example Usage**:
```python
result = await tab_oauth_client_credentials(
    ctx,
    client_id="your_client_id",
    client_secret="your_client_secret"
)
```

**Limitations**:
- Read-only access
- Cannot place bets or access account data
- Suitable for odds checking, form guides, results

---

## Racing API Tools

Comprehensive racing data access covering meetings, races, runners, and betting pools.


### 4. racing_get_all_meeting_dates

Get all available racing meeting dates.

**Use Case**: Discover available race dates for planning.

**Parameters**:
- `access_token` (str): Valid OAuth access token
- `jurisdiction` (Optional[str]): Filter by jurisdiction (NSW, VIC, QLD, SA, TAS, ACT, NT). Defaults to session config.
- `race_type` (Optional[str]): Filter by race type:
  - `"R"` - Thoroughbred racing
  - `"H"` - Harness racing  
  - `"G"` - Greyhound racing

**Returns**:
```json
{
  "dates": [
    {
      "date": "2024-10-29",
      "meeting_count": 8
    },
    {
      "date": "2024-10-30",
      "meeting_count": 12
    }
  ]
}
```

**Example Usage**:
```python
# All meetings
result = await racing_get_all_meeting_dates(ctx, access_token)

# NSW thoroughbred racing only
result = await racing_get_all_meeting_dates(
    ctx, 
    access_token,
    jurisdiction="NSW",
    race_type="R"
)
```

---

### 5. racing_get_meetings

Get all racing meetings for a specific date.

**Use Case**: View all race tracks running on a given day.

**Parameters**:
- `access_token` (str): Valid OAuth access token
- `meeting_date` (str): Date in format "YYYY-MM-DD"
- `jurisdiction` (Optional[str]): Filter by jurisdiction. Defaults to session config.
- `race_type` (Optional[str]): Filter by race type (R/H/G)

**Returns**:
```json
{
  "meetings": [
    {
      "meeting_id": "12345",
      "meeting_name": "Flemington",
      "meeting_date": "2024-10-29",
      "jurisdiction": "VIC",
      "race_type": "R",
      "track_condition": "Good 4",
      "weather": "Fine",
      "rail_position": "True"
    }
  ]
}
```

**Example Usage**:
```python
result = await racing_get_meetings(
    ctx,
    access_token,
    meeting_date="2024-10-29",
    jurisdiction="VIC",
    race_type="R"
)
```

---

### 6. racing_get_all_races_in_meeting

Get all races in a specific meeting.

**Use Case**: View race card for a particular track.

**Parameters**:
- `access_token` (str): Valid OAuth access token
- `meeting_id` (str): Unique meeting identifier
- `fixed_odds` (Optional[bool]): Include fixed odds data. Default: False

**Returns**:
```json
{
  "meeting_id": "12345",
  "races": [
    {
      "race_number": 1,
      "race_name": "Maiden Plate",
      "race_distance": 1200,
      "start_time": "2024-10-29T13:00:00Z",
      "race_status": "Open",
      "runner_count": 14
    }
  ]
}
```

**Example Usage**:
```python
# Basic race list
result = await racing_get_all_races_in_meeting(ctx, access_token, "12345")

# With fixed odds
result = await racing_get_all_races_in_meeting(
    ctx, 
    access_token, 
    "12345",
    fixed_odds=True
)
```

---

### 7. racing_get_race

Get detailed information for a specific race.

**Use Case**: Analyze race details, runners, and betting markets.

**Parameters**:
- `access_token` (str): Valid OAuth access token
- `meeting_id` (str): Meeting identifier
- `race_number` (int): Race number (1-12 typically)
- `fixed_odds` (Optional[bool]): Include fixed odds. Default: False

**Returns**:
```json
{
  "race_number": 7,
  "race_name": "Group 1 Stakes",
  "distance": 1600,
  "start_time": "2024-10-29T15:30:00Z",
  "prize_money": 500000,
  "runners": [
    {
      "runner_number": 1,
      "runner_name": "Winx",
      "barrier": 4,
      "jockey": "H Bowman",
      "trainer": "C Waller",
      "weight": 57.0,
      "odds": 2.50
    }
  ]
}
```

**Example Usage**:
```python
result = await racing_get_race(
    ctx,
    access_token,
    meeting_id="12345",
    race_number=7,
    fixed_odds=True
)
```

---

### 8. racing_get_next_to_go

Get next-to-go races ordered by start time.

**Use Case**: Quick access to upcoming races for immediate betting.

**Parameters**:
- `access_token` (str): Valid OAuth access token
- `jurisdiction` (Optional[str]): Filter by jurisdiction
- `race_type` (Optional[str]): Filter by race type (R/H/G)
- `count` (Optional[int]): Number of races to return. Default: 10

**Returns**:
```json
{
  "races": [
    {
      "meeting_name": "Randwick",
      "race_number": 3,
      "start_time": "2024-10-29T14:15:00Z",
      "minutes_to_start": 5,
      "race_type": "R"
    }
  ]
}
```

**Example Usage**:
```python
# Next 5 races
result = await racing_get_next_to_go(ctx, access_token, count=5)

# Next VIC thoroughbred races
result = await racing_get_next_to_go(
    ctx,
    access_token,
    jurisdiction="VIC",
    race_type="R",
    count=3
)
```

---


### 9. racing_get_race_form

Get comprehensive form guide for a race.

**Use Case**: Detailed analysis including runner history, jockey/trainer stats.

**Parameters**:
- `access_token` (str): Valid OAuth access token
- `meeting_id` (str): Meeting identifier
- `race_number` (int): Race number

**Returns**:
```json
{
  "race_number": 4,
  "form_guide": {
    "runners": [
      {
        "number": 1,
        "name": "Star Performer",
        "jockey": "J McDonald",
        "trainer": "G Waterhouse",
        "last_5_starts": "1-2-1-3-1",
        "career_stats": {
          "starts": 15,
          "wins": 8,
          "places": 4,
          "prize_money": 850000
        },
        "track_stats": {
          "starts": 3,
          "wins": 2,
          "places": 1
        }
      }
    ]
  }
}
```

**Example Usage**:
```python
result = await racing_get_race_form(
    ctx,
    access_token,
    meeting_id="12345",
    race_number=4
)
```

---

### 10. racing_get_runner_form

Get detailed form for a specific runner.

**Use Case**: Deep dive into individual horse/greyhound performance.

**Parameters**:
- `access_token` (str): Valid OAuth access token
- `meeting_id` (str): Meeting identifier  
- `race_number` (int): Race number
- `runner_number` (int): Runner/tab number

**Returns**:
```json
{
  "runner_number": 5,
  "name": "Lightning Bolt",
  "age": 4,
  "sex": "Gelding",
  "color": "Bay",
  "sire": "Fastnet Rock",
  "dam": "Lightning Strike",
  "form_history": [
    {
      "date": "2024-10-15",
      "track": "Randwick",
      "distance": 1400,
      "position": 1,
      "margin": 2.5,
      "time": "1:23.45",
      "weight": 56.5,
      "jockey": "J McDonald"
    }
  ],
  "statistics": {
    "career_starts": 20,
    "wins": 8,
    "win_percentage": 40.0,
    "earnings": 1250000
  }
}
```

**Example Usage**:
```python
result = await racing_get_runner_form(
    ctx,
    access_token,
    meeting_id="12345",
    race_number=4,
    runner_number=5
)
```

---

### 11. racing_get_approximates

Get pool approximate dividend projections.

**Use Case**: Real-time betting pool estimates before race start.

**Parameters**:
- `access_token` (str): Valid OAuth access token
- `meeting_id` (str): Meeting identifier
- `race_number` (int): Race number

**Returns**:
```json
{
  "race_number": 3,
  "pools": {
    "win": {
      "total_pool": 125000,
      "approximates": [
        {"runner": 1, "dividend": 3.20},
        {"runner": 2, "dividend": 5.50},
        {"runner": 3, "dividend": 8.00}
      ]
    },
    "place": {
      "total_pool": 45000,
      "approximates": [
        {"runner": 1, "dividend": 1.60},
        {"runner": 2, "dividend": 2.20}
      ]
    },
    "exacta": {
      "total_pool": 75000,
      "popular_combinations": [
        {"combination": "1-2", "dividend": 12.50},
        {"combination": "2-1", "dividend": 18.00}
      ]
    }
  }
}
```

**Example Usage**:
```python
result = await racing_get_approximates(
    ctx,
    access_token,
    meeting_id="12345",
    race_number=3
)
```

---

### 12. racing_get_open_jackpots

Get all currently open jackpots across all meetings.

**Use Case**: Identify high-value jackpot opportunities.

**Parameters**:
- `access_token` (str): Valid OAuth access token

**Returns**:
```json
{
  "jackpots": [
    {
      "jackpot_type": "Quaddie",
      "meeting_name": "Flemington",
      "meeting_date": "2024-10-29",
      "race_numbers": [5, 6, 7, 8],
      "estimated_pool": 500000,
      "carryover": 150000,
      "status": "Open"
    },
    {
      "jackpot_type": "Early Quaddie",
      "meeting_name": "Randwick",
      "meeting_date": "2024-10-29",
      "race_numbers": [1, 2, 3, 4],
      "estimated_pool": 250000,
      "carryover": 0,
      "status": "Open"
    }
  ]
}
```

**Example Usage**:
```python
result = await racing_get_open_jackpots(ctx, access_token)
```

---

### 13. racing_get_jackpot_pools

Get all jackpot pools for a specific date.

**Use Case**: Daily jackpot pool overview for strategic betting.

**Parameters**:
- `access_token` (str): Valid OAuth access token
- `meeting_date` (str): Date in format "YYYY-MM-DD"
- `jurisdiction` (Optional[str]): Filter by jurisdiction

**Returns**:
```json
{
  "date": "2024-10-29",
  "pools": [
    {
      "pool_type": "Quaddie",
      "meeting": "Flemington",
      "races": [5, 6, 7, 8],
      "pool_size": 500000,
      "carryover": 150000,
      "estimated_dividend": 25000,
      "status": "Open"
    },
    {
      "pool_type": "First Four",
      "meeting": "Randwick",
      "race": 7,
      "pool_size": 100000,
      "carryover": 0,
      "status": "Open"
    }
  ]
}
```

**Example Usage**:
```python
# All jackpots for date
result = await racing_get_jackpot_pools(
    ctx,
    access_token,
    meeting_date="2024-10-29"
)

# NSW only
result = await racing_get_jackpot_pools(
    ctx,
    access_token,
    meeting_date="2024-10-29",
    jurisdiction="NSW"
)
```

---

## Sports API Tools

Access to sports betting markets including major leagues and tournaments.


### 14. sports_get_all_open

Get all sports with at least one open or suspended market.

**Use Case**: Discover available sports for betting.

**Parameters**:
- `access_token` (str): Valid OAuth access token

**Returns**:
```json
{
  "sports": [
    {
      "sport_id": "FOOT",
      "sport_name": "Soccer",
      "open_markets": 245,
      "suspended_markets": 12
    },
    {
      "sport_id": "BASK",
      "sport_name": "Basketball",
      "open_markets": 89,
      "suspended_markets": 3
    },
    {
      "sport_id": "TENN",
      "sport_name": "Tennis",
      "open_markets": 156,
      "suspended_markets": 8
    }
  ]
}
```

**Example Usage**:
```python
result = await sports_get_all_open(ctx, access_token)
```

---

### 15. sports_get_open_sport

Get details for a specific sport with open markets.

**Use Case**: View competitions and tournaments available for a sport.

**Parameters**:
- `access_token` (str): Valid OAuth access token
- `sport_id` (str): Sport identifier (e.g., "FOOT", "BASK", "TENN")

**Returns**:
```json
{
  "sport_id": "FOOT",
  "sport_name": "Soccer",
  "competitions": [
    {
      "competition_id": "EPL",
      "competition_name": "English Premier League",
      "open_matches": 10
    },
    {
      "competition_id": "LALIGA",
      "competition_name": "La Liga",
      "open_matches": 8
    }
  ],
  "tournaments": [
    {
      "tournament_id": "UCL",
      "tournament_name": "UEFA Champions League",
      "open_matches": 16
    }
  ]
}
```

**Example Usage**:
```python
# Soccer markets
result = await sports_get_open_sport(ctx, access_token, "FOOT")

# Basketball markets
result = await sports_get_open_sport(ctx, access_token, "BASK")
```

---

### 16. sports_get_open_competition

Get a specific competition with open markets.

**Use Case**: View matches in a league or competition.

**Parameters**:
- `access_token` (str): Valid OAuth access token
- `sport_id` (str): Sport identifier
- `competition_id` (str): Competition identifier (e.g., "EPL", "NBA")

**Returns**:
```json
{
  "competition_id": "EPL",
  "competition_name": "English Premier League",
  "sport": "Soccer",
  "matches": [
    {
      "match_id": "12345",
      "home_team": "Manchester United",
      "away_team": "Liverpool",
      "start_time": "2024-10-29T15:00:00Z",
      "markets": [
        {
          "market_type": "Match Winner",
          "selections": [
            {"name": "Manchester United", "odds": 2.80},
            {"name": "Draw", "odds": 3.20},
            {"name": "Liverpool", "odds": 2.50}
          ]
        }
      ]
    }
  ]
}
```

**Example Usage**:
```python
result = await sports_get_open_competition(
    ctx,
    access_token,
    sport_id="FOOT",
    competition_id="EPL"
)
```

---

### 17. sports_get_open_tournament

Get a specific tournament with open markets.

**Use Case**: View matches in tournaments (e.g., ATP tournaments, World Cup).

**Parameters**:
- `access_token` (str): Valid OAuth access token
- `sport_id` (str): Sport identifier
- `tournament_id` (str): Tournament identifier

**Returns**:
```json
{
  "tournament_id": "AUSOPEN",
  "tournament_name": "Australian Open",
  "sport": "Tennis",
  "stage": "Quarter Finals",
  "matches": [
    {
      "match_id": "67890",
      "player1": "N. Djokovic",
      "player2": "R. Nadal",
      "start_time": "2024-10-29T09:00:00Z",
      "markets": [
        {
          "market_type": "Match Winner",
          "selections": [
            {"name": "N. Djokovic", "odds": 1.85},
            {"name": "R. Nadal", "odds": 2.00}
          ]
        },
        {
          "market_type": "Total Sets",
          "selections": [
            {"name": "Over 3.5", "odds": 1.75},
            {"name": "Under 3.5", "odds": 2.10}
          ]
        }
      ]
    }
  ]
}
```

**Example Usage**:
```python
result = await sports_get_open_tournament(
    ctx,
    access_token,
    sport_id="TENN",
    tournament_id="AUSOPEN"
)
```

---

### 18. sports_get_open_match_in_competition

Get a specific match with open markets in a competition.

**Use Case**: Detailed view of betting markets for a specific game.

**Parameters**:
- `access_token` (str): Valid OAuth access token
- `sport_id` (str): Sport identifier
- `competition_id` (str): Competition identifier
- `match_id` (str): Match identifier

**Returns**:
```json
{
  "match_id": "12345",
  "competition": "English Premier League",
  "home_team": "Manchester United",
  "away_team": "Liverpool",
  "start_time": "2024-10-29T15:00:00Z",
  "venue": "Old Trafford",
  "markets": [
    {
      "market_type": "Match Winner",
      "market_id": "MW_12345",
      "status": "Open",
      "selections": [
        {"id": "1", "name": "Manchester United", "odds": 2.80},
        {"id": "X", "name": "Draw", "odds": 3.20},
        {"id": "2", "name": "Liverpool", "odds": 2.50}
      ]
    },
    {
      "market_type": "Total Goals",
      "market_id": "TG_12345",
      "status": "Open",
      "selections": [
        {"name": "Over 2.5", "odds": 1.85},
        {"name": "Under 2.5", "odds": 2.00}
      ]
    },
    {
      "market_type": "Both Teams to Score",
      "market_id": "BTTS_12345",
      "status": "Open",
      "selections": [
        {"name": "Yes", "odds": 1.70},
        {"name": "No", "odds": 2.20}
      ]
    }
  ]
}
```

**Example Usage**:
```python
result = await sports_get_open_match_in_competition(
    ctx,
    access_token,
    sport_id="FOOT",
    competition_id="EPL",
    match_id="12345"
)
```

---

### 19. sports_get_open_match_in_tournament

Get a specific match with open markets in a tournament.

**Use Case**: Tournament match betting markets (similar to competition matches).

**Parameters**:
- `access_token` (str): Valid OAuth access token
- `sport_id` (str): Sport identifier
- `tournament_id` (str): Tournament identifier
- `match_id` (str): Match identifier

**Returns**: Same structure as `sports_get_open_match_in_competition`

**Example Usage**:
```python
result = await sports_get_open_match_in_tournament(
    ctx,
    access_token,
    sport_id="TENN",
    tournament_id="AUSOPEN",
    match_id="67890"
)
```

---

### 20. sports_get_next_to_go

Get next-to-go sports matches ordered by start time.

**Use Case**: Quick access to upcoming sporting events.

**Parameters**:
- `access_token` (str): Valid OAuth access token
- `sport_id` (Optional[str]): Filter by sport. If omitted, returns all sports.
- `count` (Optional[int]): Number of matches to return. Default: 10

**Returns**:
```json
{
  "matches": [
    {
      "match_id": "12345",
      "sport": "Soccer",
      "competition": "English Premier League",
      "home_team": "Manchester United",
      "away_team": "Liverpool",
      "start_time": "2024-10-29T15:00:00Z",
      "minutes_to_start": 30,
      "markets_available": 15
    },
    {
      "match_id": "67890",
      "sport": "Basketball",
      "competition": "NBA",
      "home_team": "Lakers",
      "away_team": "Celtics",
      "start_time": "2024-10-29T16:00:00Z",
      "minutes_to_start": 90,
      "markets_available": 12
    }
  ]
}
```

**Example Usage**:
```python
# Next 5 matches across all sports
result = await sports_get_next_to_go(ctx, access_token, count=5)

# Next 3 soccer matches
result = await sports_get_next_to_go(
    ctx,
    access_token,
    sport_id="FOOT",
    count=3
)
```

---

## Sports Results Tools

Access to completed sports events and their results.


### 21. sports_get_all_results

Get all sports with at least one resulted market.

**Use Case**: Find sports with recently completed events.

**Parameters**:
- `access_token` (str): Valid OAuth access token

**Returns**:
```json
{
  "sports": [
    {
      "sport_id": "FOOT",
      "sport_name": "Soccer",
      "resulted_markets": 125,
      "last_result_time": "2024-10-29T14:30:00Z"
    },
    {
      "sport_id": "BASK",
      "sport_name": "Basketball",
      "resulted_markets": 45,
      "last_result_time": "2024-10-29T13:15:00Z"
    }
  ]
}
```

**Example Usage**:
```python
result = await sports_get_all_results(ctx, access_token)
```

---

### 22. sports_get_resulted_sport

Get a specific sport with resulted markets.

**Use Case**: View completed competitions and tournaments for a sport.

**Parameters**:
- `access_token` (str): Valid OAuth access token
- `sport_id` (str): Sport identifier

**Returns**:
```json
{
  "sport_id": "FOOT",
  "sport_name": "Soccer",
  "competitions": [
    {
      "competition_id": "EPL",
      "competition_name": "English Premier League",
      "resulted_matches": 38
    }
  ],
  "recent_results": [
    {
      "match_id": "11111",
      "home_team": "Arsenal",
      "away_team": "Chelsea",
      "score": "2-1",
      "result_time": "2024-10-29T12:00:00Z"
    }
  ]
}
```

**Example Usage**:
```python
result = await sports_get_resulted_sport(ctx, access_token, "FOOT")
```

---

### 23. sports_get_resulted_competition

Get a specific competition with resulted markets.

**Use Case**: View completed matches in a league.

**Parameters**:
- `access_token` (str): Valid OAuth access token
- `sport_id` (str): Sport identifier
- `competition_id` (str): Competition identifier

**Returns**:
```json
{
  "competition_id": "EPL",
  "competition_name": "English Premier League",
  "sport": "Soccer",
  "matches": [
    {
      "match_id": "11111",
      "home_team": "Arsenal",
      "away_team": "Chelsea",
      "final_score": "2-1",
      "half_time_score": "1-0",
      "result_time": "2024-10-29T12:00:00Z",
      "settled_markets": [
        {
          "market_type": "Match Winner",
          "winning_selection": "Arsenal",
          "dividend": 2.50
        },
        {
          "market_type": "Total Goals",
          "winning_selection": "Over 2.5",
          "dividend": 1.85
        }
      ]
    }
  ]
}
```

**Example Usage**:
```python
result = await sports_get_resulted_competition(
    ctx,
    access_token,
    sport_id="FOOT",
    competition_id="EPL"
)
```

---

### 24. sports_get_resulted_match_in_competition

Get a specific match with results in a competition.

**Use Case**: Detailed results and dividends for a completed match.

**Parameters**:
- `access_token` (str): Valid OAuth access token
- `sport_id` (str): Sport identifier
- `competition_id` (str): Competition identifier
- `match_id` (str): Match identifier

**Returns**:
```json
{
  "match_id": "11111",
  "competition": "English Premier League",
  "home_team": "Arsenal",
  "away_team": "Chelsea",
  "final_score": "2-1",
  "half_time_score": "1-0",
  "result_time": "2024-10-29T12:00:00Z",
  "scorers": [
    {"player": "Saka", "team": "Arsenal", "minute": 23},
    {"player": "Sterling", "team": "Chelsea", "minute": 56},
    {"player": "Martinelli", "team": "Arsenal", "minute": 78}
  ],
  "settled_markets": [
    {
      "market_type": "Match Winner",
      "winning_selection": "Arsenal",
      "dividend": 2.50,
      "total_pool": 125000
    },
    {
      "market_type": "Total Goals",
      "winning_selection": "Over 2.5",
      "dividend": 1.85,
      "total_pool": 85000
    },
    {
      "market_type": "Both Teams to Score",
      "winning_selection": "Yes",
      "dividend": 1.70,
      "total_pool": 65000
    }
  ]
}
```

**Example Usage**:
```python
result = await sports_get_resulted_match_in_competition(
    ctx,
    access_token,
    sport_id="FOOT",
    competition_id="EPL",
    match_id="11111"
)
```

---

## FootyTAB Tools

Specialized tools for AFL/NRL tipping competitions and rounds.

### 25. footytab_get_all_rounds

Get all available FootyTAB rounds.

**Use Case**: View tipping competition rounds for AFL/NRL.

**Parameters**:
- `access_token` (str): Valid OAuth access token
- `competition` (Optional[str]): Filter by competition ("AFL", "NRL")

**Returns**:
```json
{
  "rounds": [
    {
      "round_id": "AFL_2024_R15",
      "competition": "AFL",
      "round_number": 15,
      "season": 2024,
      "start_date": "2024-06-20",
      "end_date": "2024-06-23",
      "matches": 9,
      "status": "Open"
    },
    {
      "round_id": "NRL_2024_R18",
      "competition": "NRL",
      "round_number": 18,
      "season": 2024,
      "start_date": "2024-07-04",
      "end_date": "2024-07-07",
      "matches": 8,
      "status": "Open"
    }
  ]
}
```

**Example Usage**:
```python
# All rounds
result = await footytab_get_all_rounds(ctx, access_token)

# AFL only
result = await footytab_get_all_rounds(ctx, access_token, competition="AFL")
```

---

### 26. footytab_get_round_details

Get detailed information for a specific FootyTAB round.

**Use Case**: View matches and tipping markets for a round.

**Parameters**:
- `access_token` (str): Valid OAuth access token
- `round_id` (str): Round identifier (e.g., "AFL_2024_R15")

**Returns**:
```json
{
  "round_id": "AFL_2024_R15",
  "competition": "AFL",
  "round_number": 15,
  "season": 2024,
  "matches": [
    {
      "match_id": "AFL_12345",
      "home_team": "Richmond",
      "away_team": "Collingwood",
      "venue": "MCG",
      "start_time": "2024-06-20T19:20:00Z",
      "markets": [
        {
          "market_type": "Head to Head",
          "selections": [
            {"team": "Richmond", "odds": 2.20},
            {"team": "Collingwood", "odds": 1.70}
          ]
        },
        {
          "market_type": "Line",
          "line": 10.5,
          "selections": [
            {"team": "Richmond +10.5", "odds": 1.90},
            {"team": "Collingwood -10.5", "odds": 1.90}
          ]
        }
      ]
    }
  ]
}
```

**Example Usage**:
```python
result = await footytab_get_round_details(ctx, access_token, "AFL_2024_R15")
```

---

## Generic API Tools

Low-level tools for custom API interactions.

### 27. tab_get

Make a generic GET request to any Tabcorp API endpoint.

**Use Case**: Access undocumented or new API endpoints.

**Parameters**:
- `access_token` (str): Valid OAuth access token
- `path` (str): API path (e.g., "/v1/racing/dates")
- `params` (Optional[Dict[str, Any]]): Query parameters

**Returns**: Raw JSON response from API

**Example Usage**:
```python
# Custom endpoint
result = await tab_get(
    ctx,
    access_token,
    path="/v1/racing/dates",
    params={"jurisdiction": "NSW"}
)

# Advanced query
result = await tab_get(
    ctx,
    access_token,
    path="/v1/sports/soccer/competitions",
    params={
        "status": "open",
        "region": "europe"
    }
)
```

**Warning**: This is a low-level tool. Prefer specific tools when available for better error handling and validation.

---

### 28. tab_post

Make a generic POST request to any Tabcorp API endpoint.

**Use Case**: Place bets or perform write operations (requires password grant auth).

**Parameters**:
- `access_token` (str): Valid OAuth access token (must have betting scope)
- `path` (str): API path (e.g., "/v1/betting/place")
- `json_body` (Optional[Dict[str, Any]]): JSON request body

**Returns**: Raw JSON response from API

**Example Usage**:
```python
# Place a bet (example structure)
result = await tab_post(
    ctx,
    access_token,
    path="/v1/betting/place",
    json_body={
        "bet_type": "WIN",
        "meeting_id": "12345",
        "race_number": 7,
        "runner_number": 5,
        "stake": 10.00
    }
)
```

**Warning**: 
- Requires password grant authentication (not client credentials)
- Real money transactions - use with caution
- Validate all parameters before calling
- Check response for errors before assuming success

---


## Common Patterns

### Authentication Flow Pattern

**Step 1: Obtain Access Token**
```python
# For personal betting (password grant)
auth_result = await tab_oauth_password_grant(
    ctx,
    client_id="your_client_id",
    client_secret="your_client_secret",
    username="your_tab_account",
    password="your_password"
)
access_token = auth_result["access_token"]
refresh_token = auth_result["refresh_token"]
expires_at = auth_result["expires_at"]

# For public data (client credentials)
auth_result = await tab_oauth_client_credentials(
    ctx,
    client_id="your_client_id",
    client_secret="your_client_secret"
)
access_token = auth_result["access_token"]
```

**Step 2: Use Token for API Calls**
```python
# Get racing data
meetings = await racing_get_meetings(
    ctx,
    access_token,
    meeting_date="2024-10-29"
)
```

**Step 3: Refresh Before Expiry**
```python
import time

if time.time() >= expires_at:
    # Token expired or about to expire
    auth_result = await tab_oauth_refresh(
        ctx,
        refresh_token=refresh_token
    )
    access_token = auth_result["access_token"]
    refresh_token = auth_result["refresh_token"]
    expires_at = auth_result["expires_at"]
```

---

### Session Configuration Pattern

**Using Session Config (Recommended)**

Store credentials in session config to avoid passing them repeatedly:

```python
# Configure once in session
ctx.session_config.client_id = "your_client_id"
ctx.session_config.client_secret = "your_client_secret"
ctx.session_config.username = "your_tab_account"
ctx.session_config.password = "your_password"
ctx.session_config.jurisdiction = "NSW"

# Tools automatically use session config
auth_result = await tab_oauth_password_grant(ctx)  # No params needed
meetings = await racing_get_meetings(ctx, access_token, "2024-10-29")  # Uses NSW jurisdiction
```

---

### Racing Workflow Pattern

**Complete Racing Analysis Flow**

```python
# 1. Authenticate
auth = await tab_oauth_client_credentials(ctx)
token = auth["access_token"]

# 2. Find upcoming races
next_races = await racing_get_next_to_go(
    ctx,
    token,
    jurisdiction="NSW",
    race_type="R",
    count=5
)

# 3. Get detailed race info
race_info = await racing_get_race(
    ctx,
    token,
    meeting_id=next_races["races"][0]["meeting_id"],
    race_number=next_races["races"][0]["race_number"],
    fixed_odds=True
)

# 4. Analyze form guide
form = await racing_get_race_form(
    ctx,
    token,
    meeting_id=next_races["races"][0]["meeting_id"],
    race_number=next_races["races"][0]["race_number"]
)

# 5. Get runner details
runner_form = await racing_get_runner_form(
    ctx,
    token,
    meeting_id=next_races["races"][0]["meeting_id"],
    race_number=next_races["races"][0]["race_number"],
    runner_number=1
)

# 6. Check pool approximates
approximates = await racing_get_approximates(
    ctx,
    token,
    meeting_id=next_races["races"][0]["meeting_id"],
    race_number=next_races["races"][0]["race_number"]
)
```

---

### Sports Workflow Pattern

**Complete Sports Betting Flow**

```python
# 1. Authenticate
auth = await tab_oauth_client_credentials(ctx)
token = auth["access_token"]

# 2. Discover available sports
sports = await sports_get_all_open(ctx, token)

# 3. Get specific sport details
soccer = await sports_get_open_sport(ctx, token, "FOOT")

# 4. Get competition details
epl = await sports_get_open_competition(
    ctx,
    token,
    sport_id="FOOT",
    competition_id="EPL"
)

# 5. Get match details with all markets
match = await sports_get_open_match_in_competition(
    ctx,
    token,
    sport_id="FOOT",
    competition_id="EPL",
    match_id=epl["matches"][0]["match_id"]
)

# 6. Check results after match
results = await sports_get_resulted_match_in_competition(
    ctx,
    token,
    sport_id="FOOT",
    competition_id="EPL",
    match_id=match["match_id"]
)
```

---

### Multi-Jurisdiction Pattern

**Compare Odds Across Jurisdictions**

```python
jurisdictions = ["NSW", "VIC", "QLD"]
token = auth["access_token"]
meeting_date = "2024-10-29"

all_meetings = {}
for jurisdiction in jurisdictions:
    meetings = await racing_get_meetings(
        ctx,
        token,
        meeting_date=meeting_date,
        jurisdiction=jurisdiction
    )
    all_meetings[jurisdiction] = meetings

# Compare and analyze
for juris, data in all_meetings.items():
    print(f"{juris}: {len(data['meetings'])} meetings")
```

---

### Jackpot Hunting Pattern

**Find Best Jackpot Opportunities**

```python
# 1. Get all open jackpots
jackpots = await racing_get_open_jackpots(ctx, token)

# 2. Filter by pool size
big_jackpots = [
    jp for jp in jackpots["jackpots"]
    if jp["estimated_pool"] >= 100000
]

# 3. Sort by carryover
big_jackpots.sort(key=lambda x: x["carryover"], reverse=True)

# 4. Get details for top opportunity
top_jackpot = big_jackpots[0]
for race_num in top_jackpot["race_numbers"]:
    race_info = await racing_get_race(
        ctx,
        token,
        meeting_id=top_jackpot["meeting_id"],
        race_number=race_num
    )
    # Analyze race_info for selections
```

---

## Error Handling

### TabcorpAPIError Exception

All tools raise `TabcorpAPIError` for API-related failures.

**Exception Attributes:**
- `message` (str): Human-readable error description
- `status_code` (Optional[int]): HTTP status code if available
- `response_data` (Optional[Dict]): Raw API error response

**Example Error Handling:**

```python
from tab_mcp.server import TabcorpAPIError

try:
    result = await tab_oauth_password_grant(
        ctx,
        client_id="invalid",
        client_secret="wrong"
    )
except TabcorpAPIError as e:
    print(f"Error: {e.message}")
    print(f"Status Code: {e.status_code}")
    print(f"Response Data: {e.response_data}")

    # Handle specific errors
    if e.status_code == 401:
        print("Authentication failed - check credentials")
    elif e.status_code == 429:
        print("Rate limit exceeded - wait before retrying")
    elif e.status_code == 503:
        print("Service unavailable - try again later")
```

---

### Common HTTP Status Codes

| Status Code | Meaning | Common Cause | Solution |
|-------------|---------|--------------|----------|
| 400 | Bad Request | Invalid parameters | Validate input parameters |
| 401 | Unauthorized | Invalid/expired token | Re-authenticate |
| 403 | Forbidden | Insufficient permissions | Use password grant for betting |
| 404 | Not Found | Invalid ID | Verify meeting/race/match IDs |
| 429 | Too Many Requests | Rate limit exceeded | Implement backoff/retry logic |
| 500 | Internal Server Error | API error | Retry with exponential backoff |
| 503 | Service Unavailable | Maintenance/overload | Wait and retry later |

---

### Network Error Handling

**Timeout Errors:**
```python
try:
    result = await racing_get_meetings(ctx, token, "2024-10-29")
except TabcorpAPIError as e:
    if "timeout" in e.message.lower():
        # Retry with backoff
        import time
        time.sleep(2)
        result = await racing_get_meetings(ctx, token, "2024-10-29")
```

**Network Errors:**
```python
try:
    result = await sports_get_all_open(ctx, token)
except TabcorpAPIError as e:
    if "network" in e.message.lower():
        # Check connectivity
        print("Network connectivity issue detected")
        # Implement retry logic or alert user
```

---

### Validation Errors

**Invalid Jurisdiction:**
```python
try:
    meetings = await racing_get_meetings(
        ctx,
        token,
        "2024-10-29",
        jurisdiction="INVALID"  # Not in NSW, VIC, QLD, SA, TAS, ACT, NT
    )
except ValueError as e:
    print(f"Validation error: {e}")
    # Use valid jurisdiction
```

**Invalid Race Type:**
```python
try:
    dates = await racing_get_all_meeting_dates(
        ctx,
        token,
        race_type="X"  # Not R, H, or G
    )
except ValueError as e:
    print(f"Invalid race type: {e}")
    # Use R, H, or G
```

---

### Retry Pattern with Exponential Backoff

```python
import time
import random

def retry_with_backoff(func, max_retries=3, base_delay=1):
    """Retry function with exponential backoff"""
    for attempt in range(max_retries):
        try:
            return func()
        except TabcorpAPIError as e:
            if e.status_code in [500, 503, 429]:  # Retryable errors
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
                    print(f"Retry {attempt + 1}/{max_retries} after {delay:.2f}s")
                    time.sleep(delay)
                else:
                    raise  # Max retries exceeded
            else:
                raise  # Non-retryable error

# Usage
result = retry_with_backoff(
    lambda: racing_get_next_to_go(ctx, token, count=5)
)
```

---

### Best Practices for Error Handling

1. **Always wrap API calls in try-except blocks**
2. **Log errors with full context** (status code, response data)
3. **Implement retry logic for transient failures** (500, 503, 429)
4. **Validate inputs before API calls** to catch errors early
5. **Monitor error rates** to detect API issues
6. **Implement circuit breaker pattern** for sustained failures
7. **Provide user-friendly error messages** in production
8. **Cache successful responses** to reduce API calls

---

## Additional Resources

### Documentation
- **[README.md](README.md)** - Quick start and overview
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Deployment procedures and runbook
- **[TESTING_SUMMARY.md](TESTING_SUMMARY.md)** - Testing infrastructure
- **[SECURITY.md](SECURITY.md)** - Security best practices
- **[DEVOPS_SUMMARY.md](DEVOPS_SUMMARY.md)** - DevOps workflows and automation

### External Links
- **Live Server**: https://server.smithery.ai/@bencousins22/tab-mcp/mcp
- **GitHub Repository**: https://github.com/bencousins22/tab-mcp
- **Smithery Platform**: https://smithery.ai
- **MCP Protocol**: https://modelcontextprotocol.io

### Support
For issues, questions, or contributions, please visit the GitHub repository.

---

**Last Updated**: October 29, 2024  
**Version**: 1.0.0  
**Maintained by**: Tabcorp MCP Server Documentation Team
