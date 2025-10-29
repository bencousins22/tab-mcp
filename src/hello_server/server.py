"""
Tabcorp API MCP Server - Production Ready
Comprehensive Model Context Protocol server for Tabcorp betting API
Enterprise-grade implementation with full error handling and validation

Version: 1.0.0
API Base: https://api.beta.tab.com.au
MCP Protocol: v1.0
"""
from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional
from datetime import datetime

import httpx
from mcp.server.fastmcp import Context, FastMCP
from pydantic import BaseModel, Field, validator
from smithery.decorators import smithery


# Constants
TAB_BASE_URL = "https://api.beta.tab.com.au"
OAUTH_TOKEN_PATH = "/oauth/token"
USER_AGENT = "tabcorp-mcp/1.0.0"
DEFAULT_TIMEOUT = 30.0
TOKEN_EXPIRY_BUFFER = 60  # Refresh tokens 60s before expiry

# Valid jurisdictions
VALID_JURISDICTIONS = {"NSW", "VIC", "QLD", "SA", "TAS", "ACT", "NT"}
VALID_RACE_TYPES = {"R", "H", "G"}  # Racing, Harness, Greyhounds

# Configure logging
logger = logging.getLogger(__name__)


class TabcorpAPIError(Exception):
    """Custom exception for Tabcorp API errors"""
    def __init__(self, message: str, status_code: Optional[int] = None, response_data: Optional[Dict] = None):
        self.message = message
        self.status_code = status_code
        self.response_data = response_data
        super().__init__(self.message)


class ConfigSchema(BaseModel):
    """Session configuration for Tabcorp API credentials and preferences"""
    client_id: Optional[str] = Field(None, description="Tabcorp OAuth client_id")
    client_secret: Optional[str] = Field(None, description="Tabcorp OAuth client_secret")
    username: Optional[str] = Field(None, description="TAB account number (for password grant)")
    password: Optional[str] = Field(None, description="TAB account password (for password grant)")
    refresh_token: Optional[str] = Field(None, description="Cached refresh token")
    jurisdiction: str = Field("NSW", description="Default jurisdiction (NSW, VIC, QLD, SA, TAS, ACT, NT)")
    base_url: str = Field(TAB_BASE_URL, description="Tabcorp API base URL")

    @validator('jurisdiction')
    def validate_jurisdiction(cls, v):
        if v not in VALID_JURISDICTIONS:
            raise ValueError(f"Invalid jurisdiction. Must be one of: {', '.join(VALID_JURISDICTIONS)}")
        return v


@smithery.server(config_schema=ConfigSchema)
def create_server() -> FastMCP:
    """Create and configure the production-ready Tabcorp MCP server"""
    server = FastMCP("Tabcorp API Server", version="1.0.0")

    # ========== Helper Functions ==========

    def _oauth_post(base_url: str, data: Dict[str, str]) -> Dict[str, Any]:
        """POST to OAuth token endpoint with comprehensive error handling"""
        url = f"{base_url.rstrip('/')}{OAUTH_TOKEN_PATH}"
        headers = {
            "content-type": "application/x-www-form-urlencoded",
            "user-agent": USER_AGENT
        }
        
        try:
            with httpx.Client(timeout=DEFAULT_TIMEOUT) as client:
                resp = client.post(url, data=data, headers=headers)
                
                # Handle HTTP errors
                if resp.status_code >= 400:
                    try:
                        error_data = resp.json()
                        error_msg = error_data.get('error_description', error_data.get('message', 'Unknown error'))
                    except Exception:
                        error_msg = resp.text or f"HTTP {resp.status_code}"
                    
                    raise TabcorpAPIError(
                        f"OAuth authentication failed: {error_msg}",
                        status_code=resp.status_code,
                        response_data=error_data if 'error_data' in locals() else None
                    )
                
                result = resp.json()
                
                # Add calculated expiry timestamp
                if "expires_in" in result:
                    result["expires_at"] = int(time.time()) + int(result["expires_in"]) - TOKEN_EXPIRY_BUFFER
                
                return result
                
        except httpx.TimeoutException:
            raise TabcorpAPIError("Request timed out. Please try again.")
        except httpx.NetworkError as e:
            raise TabcorpAPIError(f"Network error: {str(e)}")
        except Exception as e:
            if isinstance(e, TabcorpAPIError):
                raise
            raise TabcorpAPIError(f"Unexpected error during authentication: {str(e)}")

    def _bearer_get(base_url: str, path: str, token: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """GET request with bearer authentication and error handling"""
        url = f"{base_url.rstrip('/')}{path if path.startswith('/') else '/' + path}"
        headers = {
            "authorization": f"Bearer {token}",
            "user-agent": USER_AGENT,
            "accept": "application/json"
        }
        
        try:
            with httpx.Client(timeout=DEFAULT_TIMEOUT) as client:
                resp = client.get(url, headers=headers, params=params or {})
                
                # Handle HTTP errors
                if resp.status_code >= 400:
                    try:
                        error_data = resp.json()
                        error_msg = error_data.get('error', {}).get('message', 'Unknown error')
                    except Exception:
                        error_msg = resp.text or f"HTTP {resp.status_code}"
                    
                    raise TabcorpAPIError(
                        f"API request failed: {error_msg}",
                        status_code=resp.status_code,
                        response_data=error_data if 'error_data' in locals() else None
                    )
                
                return resp.json()
                
        except httpx.TimeoutException:
            raise TabcorpAPIError("Request timed out. Please try again.")
        except httpx.NetworkError as e:
            raise TabcorpAPIError(f"Network error: {str(e)}")
        except Exception as e:
            if isinstance(e, TabcorpAPIError):
                raise
            raise TabcorpAPIError(f"Unexpected error during API request: {str(e)}")

    def _bearer_post(base_url: str, path: str, token: str, json_body: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """POST request with bearer authentication and error handling"""
        url = f"{base_url.rstrip('/')}{path if path.startswith('/') else '/' + path}"
        headers = {
            "authorization": f"Bearer {token}",
            "user-agent": USER_AGENT,
            "content-type": "application/json",
            "accept": "application/json"
        }
        
        try:
            with httpx.Client(timeout=DEFAULT_TIMEOUT) as client:
                resp = client.post(url, headers=headers, json=json_body or {})
                
                # Handle HTTP errors
                if resp.status_code >= 400:
                    try:
                        error_data = resp.json()
                        error_msg = error_data.get('error', {}).get('message', 'Unknown error')
                    except Exception:
                        error_msg = resp.text or f"HTTP {resp.status_code}"
                    
                    raise TabcorpAPIError(
                        f"API request failed: {error_msg}",
                        status_code=resp.status_code,
                        response_data=error_data if 'error_data' in locals() else None
                    )
                
                return resp.json()
                
        except httpx.TimeoutException:
            raise TabcorpAPIError("Request timed out. Please try again.")
        except httpx.NetworkError as e:
            raise TabcorpAPIError(f"Network error: {str(e)}")
        except Exception as e:
            if isinstance(e, TabcorpAPIError):
                raise
            raise TabcorpAPIError(f"Unexpected error during API request: {str(e)}")

    def _validate_jurisdiction(jurisdiction: Optional[str], cfg: ConfigSchema) -> str:
        """Validate and return jurisdiction"""
        j = (jurisdiction or cfg.jurisdiction).upper()
        if j not in VALID_JURISDICTIONS:
            raise ValueError(f"Invalid jurisdiction '{j}'. Must be one of: {', '.join(VALID_JURISDICTIONS)}")
        return j

    def _validate_race_type(race_type: str) -> str:
        """Validate race type"""
        rt = race_type.upper()
        if rt not in VALID_RACE_TYPES:
            raise ValueError(f"Invalid race type '{rt}'. Must be one of: R (Racing), H (Harness), G (Greyhounds)")
        return rt

    # ========== OAuth Authentication Tools ==========

    @server.tool()
    def tab_oauth_password_grant(
        ctx: Context,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Obtain access and refresh tokens via password grant (for personal account betting).
        
        Args:
            client_id: Tabcorp OAuth client ID (from config if not provided)
            client_secret: Tabcorp OAuth client secret (from config if not provided)
            username: TAB account number (from config if not provided)
            password: TAB account password (from config if not provided)
        
        Returns:
            Dict containing access_token, refresh_token, expires_in, expires_at, token_type
        
        Raises:
            TabcorpAPIError: If authentication fails or credentials are invalid
        """
        cfg: ConfigSchema = ctx.session_config
        data = {
            "grant_type": "password",
            "client_id": client_id or cfg.client_id,
            "client_secret": client_secret or cfg.client_secret,
            "username": username or cfg.username,
            "password": password or cfg.password,
        }
        
        missing = [k for k, v in data.items() if k != "grant_type" and not v]
        if missing:
            raise ValueError(f"Missing required credentials: {', '.join(missing)}. Provide via arguments or session config.")
        
        return _oauth_post(cfg.base_url, data)

    @server.tool()
    def tab_oauth_refresh(
        ctx: Context,
        refresh_token: Optional[str] = None,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Refresh access token using refresh_token grant.
        
        Args:
            refresh_token: The refresh token (from config if not provided)
            client_id: Tabcorp OAuth client ID (from config if not provided)
            client_secret: Tabcorp OAuth client secret (from config if not provided)
        
        Returns:
            Dict containing new access_token, refresh_token, expires_in, expires_at, token_type
        
        Raises:
            TabcorpAPIError: If token refresh fails
        """
        cfg: ConfigSchema = ctx.session_config
        data = {
            "grant_type": "refresh_token",
            "client_id": client_id or cfg.client_id,
            "client_secret": client_secret or cfg.client_secret,
            "refresh_token": refresh_token or cfg.refresh_token,
        }
        
        missing = [k for k, v in data.items() if k != "grant_type" and not v]
        if missing:
            raise ValueError(f"Missing required credentials: {', '.join(missing)}")
        
        return _oauth_post(cfg.base_url, data)

    @server.tool()
    def tab_oauth_client_credentials(
        ctx: Context,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Obtain token via client_credentials grant (for public data, no account needed).
        
        Args:
            client_id: Tabcorp OAuth client ID (from config if not provided)
            client_secret: Tabcorp OAuth client secret (from config if not provided)
        
        Returns:
            Dict containing access_token, expires_in, expires_at, token_type
        
        Raises:
            TabcorpAPIError: If authentication fails
        """
        cfg: ConfigSchema = ctx.session_config
        data = {
            "grant_type": "client_credentials",
            "client_id": client_id or cfg.client_id,
            "client_secret": client_secret or cfg.client_secret,
        }
        
        missing = [k for k, v in data.items() if k != "grant_type" and not v]
        if missing:
            raise ValueError(f"Missing required credentials: {', '.join(missing)}")
        
        return _oauth_post(cfg.base_url, data)

    # ========== Racing Endpoints ==========

    @server.tool()
    def racing_get_all_meeting_dates(
        ctx: Context,
        access_token: str,
        jurisdiction: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get all available racing meeting dates including today, tomorrow, and futures."""
        cfg: ConfigSchema = ctx.session_config
        params = {"jurisdiction": _validate_jurisdiction(jurisdiction, cfg)}
        return _bearer_get(cfg.base_url, "/v1/tab-info-service/racing/dates", access_token, params)

    @server.tool()
    def racing_get_meetings(
        ctx: Context,
        access_token: str,
        meeting_date: str,
        jurisdiction: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get all meetings for a specific date.
        
        Args:
            access_token: Bearer access token
            meeting_date: Date in YYYY-MM-DD format (e.g., '2025-10-29')
            jurisdiction: Jurisdiction code (NSW, VIC, etc.)
        """
        cfg: ConfigSchema = ctx.session_config
        params = {"jurisdiction": _validate_jurisdiction(jurisdiction, cfg)}
        return _bearer_get(cfg.base_url, f"/v1/tab-info-service/racing/dates/{meeting_date}/meetings", access_token, params)

    @server.tool()
    def racing_get_all_races_in_meeting(
        ctx: Context,
        access_token: str,
        meeting_date: str,
        race_type: str,
        venue_mnemonic: str,
        jurisdiction: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get all races in a meeting.
        
        Args:
            race_type: R (Racing/Thoroughbred), H (Harness), G (Greyhounds)
            venue_mnemonic: Three-letter venue code (e.g., 'RAN' for Randwick)
        """
        cfg: ConfigSchema = ctx.session_config
        race_type = _validate_race_type(race_type)
        params = {"jurisdiction": _validate_jurisdiction(jurisdiction, cfg)}
        path = f"/v1/tab-info-service/racing/dates/{meeting_date}/meetings/{race_type}/{venue_mnemonic}/races"
        return _bearer_get(cfg.base_url, path, access_token, params)

    @server.tool()
    def racing_get_race(
        ctx: Context,
        access_token: str,
        meeting_date: str,
        race_type: str,
        venue_mnemonic: str,
        race_number: int,
        jurisdiction: Optional[str] = None,
        fixed_odds: bool = False,
    ) -> Dict[str, Any]:
        """Get detailed information for a specific race including runners, odds, and pools."""
        cfg: ConfigSchema = ctx.session_config
        race_type = _validate_race_type(race_type)
        params = {
            "jurisdiction": _validate_jurisdiction(jurisdiction, cfg),
            "fixedOdds": str(fixed_odds).lower()
        }
        path = f"/v1/tab-info-service/racing/dates/{meeting_date}/meetings/{race_type}/{venue_mnemonic}/races/{race_number}"
        return _bearer_get(cfg.base_url, path, access_token, params)

    @server.tool()
    def racing_get_next_to_go(
        ctx: Context,
        access_token: str,
        jurisdiction: Optional[str] = None,
        max_races: Optional[int] = None,
        include_recently_closed: bool = False,
    ) -> Dict[str, Any]:
        """Get next-to-go races ordered by start time."""
        cfg: ConfigSchema = ctx.session_config
        params: Dict[str, Any] = {"jurisdiction": _validate_jurisdiction(jurisdiction, cfg)}
        if max_races:
            params["maxRaces"] = max_races
        if include_recently_closed:
            params["includeRecentlyClosed"] = "true"
        return _bearer_get(cfg.base_url, "/v1/tab-info-service/racing/next-to-go/races", access_token, params)

    @server.tool()
    def racing_get_race_form(
        ctx: Context,
        access_token: str,
        meeting_date: str,
        race_type: str,
        venue_mnemonic: str,
        race_number: int,
        jurisdiction: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get comprehensive form guide for a race including all runners and their recent performance."""
        cfg: ConfigSchema = ctx.session_config
        race_type = _validate_race_type(race_type)
        params = {"jurisdiction": _validate_jurisdiction(jurisdiction, cfg)}
        path = f"/v1/tab-info-service/racing/dates/{meeting_date}/meetings/{race_type}/{venue_mnemonic}/races/{race_number}/form"
        return _bearer_get(cfg.base_url, path, access_token, params)

    @server.tool()
    def racing_get_runner_form(
        ctx: Context,
        access_token: str,
        meeting_date: str,
        race_type: str,
        venue_mnemonic: str,
        race_number: int,
        runner_number: str,
        jurisdiction: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get detailed form guide for a specific runner including past performances and statistics."""
        cfg: ConfigSchema = ctx.session_config
        race_type = _validate_race_type(race_type)
        params = {"jurisdiction": _validate_jurisdiction(jurisdiction, cfg)}
        path = f"/v1/tab-info-service/racing/dates/{meeting_date}/meetings/{race_type}/{venue_mnemonic}/races/{race_number}/form/{runner_number}"
        return _bearer_get(cfg.base_url, path, access_token, params)

    @server.tool()
    def racing_get_approximates(
        ctx: Context,
        access_token: str,
        meeting_date: str,
        race_type: str,
        venue_mnemonic: str,
        race_number: int,
        wagering_product: str,
        jurisdiction: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get pool approximates for a race.
        
        Args:
            wagering_product: WIN, PLACE, QUINELLA, EXACTA, TRIFECTA, FIRST4, etc.
        """
        cfg: ConfigSchema = ctx.session_config
        race_type = _validate_race_type(race_type)
        params = {"jurisdiction": _validate_jurisdiction(jurisdiction, cfg)}
        path = f"/v1/tab-info-service/racing/dates/{meeting_date}/meetings/{race_type}/{venue_mnemonic}/races/{race_number}/pools/{wagering_product}/approximates"
        return _bearer_get(cfg.base_url, path, access_token, params)

    @server.tool()
    def racing_get_open_jackpots(
        ctx: Context,
        access_token: str,
        jurisdiction: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get all currently open jackpots across all meetings."""
        cfg: ConfigSchema = ctx.session_config
        params = {"jurisdiction": _validate_jurisdiction(jurisdiction, cfg)}
        return _bearer_get(cfg.base_url, "/v1/tab-info-service/racing/jackpots", access_token, params)

    @server.tool()
    def racing_get_jackpot_pools(
        ctx: Context,
        access_token: str,
        meeting_date: str,
        jurisdiction: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get all jackpot pools for a specific date."""
        cfg: ConfigSchema = ctx.session_config
        params = {"jurisdiction": _validate_jurisdiction(jurisdiction, cfg)}
        return _bearer_get(cfg.base_url, f"/v1/tab-info-service/racing/dates/{meeting_date}/jackpot-pools", access_token, params)

    # ========== Sports Endpoints ==========

    @server.tool()
    def sports_get_all_open(
        ctx: Context,
        access_token: str,
        jurisdiction: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get all sports with at least one open or suspended market."""
        cfg: ConfigSchema = ctx.session_config
        params = {"jurisdiction": _validate_jurisdiction(jurisdiction, cfg)}
        return _bearer_get(cfg.base_url, "/v1/tab-info-service/sports", access_token, params)

    @server.tool()
    def sports_get_open_sport(
        ctx: Context,
        access_token: str,
        sport_name: str,
        jurisdiction: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get a specific sport with open markets.
        
        Args:
            sport_name: e.g., 'Basketball', 'Rugby League', 'AFL', 'Tennis', 'Soccer'
        """
        cfg: ConfigSchema = ctx.session_config
        params = {"jurisdiction": _validate_jurisdiction(jurisdiction, cfg)}
        return _bearer_get(cfg.base_url, f"/v1/tab-info-service/sports/{sport_name}", access_token, params)

    @server.tool()
    def sports_get_open_competition(
        ctx: Context,
        access_token: str,
        sport_name: str,
        competition_name: str,
        jurisdiction: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get a specific competition with open markets.
        
        Args:
            sport_name: e.g., 'Basketball'
            competition_name: e.g., 'NBA', 'NBL'
        """
        cfg: ConfigSchema = ctx.session_config
        params = {"jurisdiction": _validate_jurisdiction(jurisdiction, cfg)}
        return _bearer_get(cfg.base_url, f"/v1/tab-info-service/sports/{sport_name}/competitions/{competition_name}", access_token, params)

    @server.tool()
    def sports_get_open_tournament(
        ctx: Context,
        access_token: str,
        sport_name: str,
        competition_name: str,
        tournament_name: str,
        jurisdiction: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get a specific tournament with open markets (e.g., ATP tournaments in Tennis)."""
        cfg: ConfigSchema = ctx.session_config
        params = {"jurisdiction": _validate_jurisdiction(jurisdiction, cfg)}
        path = f"/v1/tab-info-service/sports/{sport_name}/competitions/{competition_name}/tournaments/{tournament_name}"
        return _bearer_get(cfg.base_url, path, access_token, params)

    @server.tool()
    def sports_get_open_match_in_competition(
        ctx: Context,
        access_token: str,
        sport_name: str,
        competition_name: str,
        match_name: str,
        jurisdiction: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get a specific match in a competition with open markets.
        
        Args:
            match_name: e.g., 'Lakers v Warriors'
        """
        cfg: ConfigSchema = ctx.session_config
        params = {"jurisdiction": _validate_jurisdiction(jurisdiction, cfg)}
        path = f"/v1/tab-info-service/sports/{sport_name}/competitions/{competition_name}/matches/{match_name}"
        return _bearer_get(cfg.base_url, path, access_token, params)

    @server.tool()
    def sports_get_open_match_in_tournament(
        ctx: Context,
        access_token: str,
        sport_name: str,
        competition_name: str,
        tournament_name: str,
        match_name: str,
        jurisdiction: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get a specific match in a tournament with open markets."""
        cfg: ConfigSchema = ctx.session_config
        params = {"jurisdiction": _validate_jurisdiction(jurisdiction, cfg)}
        path = f"/v1/tab-info-service/sports/{sport_name}/competitions/{competition_name}/tournaments/{tournament_name}/matches/{match_name}"
        return _bearer_get(cfg.base_url, path, access_token, params)

    @server.tool()
    def sports_get_next_to_go(
        ctx: Context,
        access_token: str,
        jurisdiction: Optional[str] = None,
        limit: Optional[int] = None,
        live_betting_only: bool = False,
        futures_only: bool = False,
        open_only: bool = False,
    ) -> Dict[str, Any]:
        """Get next-to-go sports matches sorted by start time with optional filters."""
        cfg: ConfigSchema = ctx.session_config
        params: Dict[str, Any] = {"jurisdiction": _validate_jurisdiction(jurisdiction, cfg)}
        if limit:
            params["limit"] = limit
        if live_betting_only:
            params["liveBettingOnly"] = "true"
        if futures_only:
            params["futuresOnly"] = "true"
        if open_only:
            params["openOnly"] = "true"
        return _bearer_get(cfg.base_url, "/v1/tab-info-service/sports/nextToGo", access_token, params)

    # ========== Sports Results Endpoints ==========

    @server.tool()
    def sports_get_all_results(
        ctx: Context,
        access_token: str,
        jurisdiction: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get all sports with at least one resulted market."""
        cfg: ConfigSchema = ctx.session_config
        params = {"jurisdiction": _validate_jurisdiction(jurisdiction, cfg)}
        return _bearer_get(cfg.base_url, "/v1/tab-info-service/sports/results", access_token, params)

    @server.tool()
    def sports_get_resulted_sport(
        ctx: Context,
        access_token: str,
        sport_name: str,
        jurisdiction: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get a specific sport with resulted markets."""
        cfg: ConfigSchema = ctx.session_config
        params = {"jurisdiction": _validate_jurisdiction(jurisdiction, cfg)}
        return _bearer_get(cfg.base_url, f"/v1/tab-info-service/sports/results/{sport_name}", access_token, params)

    @server.tool()
    def sports_get_resulted_competition(
        ctx: Context,
        access_token: str,
        sport_name: str,
        competition_name: str,
        jurisdiction: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get a specific competition with resulted markets."""
        cfg: ConfigSchema = ctx.session_config
        params = {"jurisdiction": _validate_jurisdiction(jurisdiction, cfg)}
        return _bearer_get(cfg.base_url, f"/v1/tab-info-service/sports/results/{sport_name}/competitions/{competition_name}", access_token, params)

    @server.tool()
    def sports_get_resulted_match_in_competition(
        ctx: Context,
        access_token: str,
        sport_name: str,
        competition_name: str,
        match_name: str,
        jurisdiction: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get a specific match with results in a competition."""
        cfg: ConfigSchema = ctx.session_config
        params = {"jurisdiction": _validate_jurisdiction(jurisdiction, cfg)}
        path = f"/v1/tab-info-service/sports/results/{sport_name}/competitions/{competition_name}/matches/{match_name}"
        return _bearer_get(cfg.base_url, path, access_token, params)

    # ========== FootyTAB Endpoints ==========

    @server.tool()
    def footytab_get_all_rounds(
        ctx: Context,
        access_token: str,
        sport_name: str,
        jurisdiction: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get all FootyTAB rounds for a sport.
        
        Args:
            sport_name: e.g., 'AFL', 'Rugby League', 'Rugby Union'
        """
        cfg: ConfigSchema = ctx.session_config
        params = {"jurisdiction": _validate_jurisdiction(jurisdiction, cfg)}
        return _bearer_get(cfg.base_url, f"/v1/tab-info-service/sports/{sport_name}/footy/rounds", access_token, params)

    @server.tool()
    def footytab_get_round_details(
        ctx: Context,
        access_token: str,
        sport_name: str,
        round_number: int,
        jurisdiction: Optional[str] = None,
        series: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get FootyTAB round details for a specific round number.
        
        Args:
            series: Optional series name for sports with multiple series
        """
        cfg: ConfigSchema = ctx.session_config
        params: Dict[str, Any] = {"jurisdiction": _validate_jurisdiction(jurisdiction, cfg)}
        if series:
            params["series"] = series
        return _bearer_get(cfg.base_url, f"/v1/tab-info-service/sports/{sport_name}/footy/rounds/{round_number}", access_token, params)

    # ========== Generic API Tools ==========

    @server.tool()
    def tab_get(
        ctx: Context,
        access_token: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        jurisdiction: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generic GET request to any Tabcorp API endpoint with bearer authentication.
        
        Args:
            path: API endpoint path (e.g., '/v1/tab-info-service/racing/dates')
            params: Optional query parameters
            jurisdiction: Optional jurisdiction override
        
        Use this for endpoints not covered by specialized tools.
        """
        cfg: ConfigSchema = ctx.session_config
        p = dict(params or {})
        if "jurisdiction" not in p and jurisdiction:
            p["jurisdiction"] = _validate_jurisdiction(jurisdiction, cfg)
        return _bearer_get(cfg.base_url, path, access_token, p)

    @server.tool()
    def tab_post(
        ctx: Context,
        access_token: str,
        path: str,
        body: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Generic POST request to any Tabcorp API endpoint with bearer authentication.
        
        Args:
            path: API endpoint path
            body: Optional JSON request body
        
        Use this for placing bets or other POST operations.
        """
        cfg: ConfigSchema = ctx.session_config
        return _bearer_post(cfg.base_url, path, access_token, body or {})

    return server
