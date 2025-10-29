"""
Tabcorp API MCP Server
Comprehensive Model Context Protocol server for Tabcorp betting API
Supports Racing, Sports, FootyTAB, and Results endpoints
"""
from __future__ import annotations

import time
from typing import Any, Dict, List, Optional
from datetime import datetime

import httpx
from mcp.server.fastmcp import Context, FastMCP
from pydantic import BaseModel, Field
from smithery.decorators import smithery


TAB_BASE_URL = "https://api.beta.tab.com.au"
OAUTH_TOKEN_PATH = "/oauth/token"
USER_AGENT = "tabcorp-mcp/1.0"
DEFAULT_TIMEOUT = 30.0


class ConfigSchema(BaseModel):
    """Session configuration for Tabcorp API credentials and preferences"""
    client_id: Optional[str] = Field(None, description="Tabcorp OAuth client_id")
    client_secret: Optional[str] = Field(None, description="Tabcorp OAuth client_secret")
    username: Optional[str] = Field(None, description="TAB account number (for password grant)")
    password: Optional[str] = Field(None, description="TAB account password (for password grant)")
    refresh_token: Optional[str] = Field(None, description="Cached refresh token")
    jurisdiction: str = Field("NSW", description="Default jurisdiction (NSW, VIC, QLD, SA, TAS, ACT, NT)")
    base_url: str = Field(TAB_BASE_URL, description="Tabcorp API base URL")


@smithery.server(config_schema=ConfigSchema)
def create_server() -> FastMCP:
    """Create and configure the Tabcorp MCP server"""
    server = FastMCP("Tabcorp API Server")

    # ========== Helper Functions ==========

    def _oauth_post(base_url: str, data: Dict[str, str]) -> Dict[str, Any]:
        """POST to OAuth token endpoint"""
        url = f"{base_url.rstrip('/')}{OAUTH_TOKEN_PATH}"
        headers = {"content-type": "application/x-www-form-urlencoded", "user-agent": USER_AGENT}
        with httpx.Client(timeout=DEFAULT_TIMEOUT) as client:
            resp = client.post(url, data=data, headers=headers)
            resp.raise_for_status()
            result = resp.json()
            # Add expires_at timestamp for convenience
            if "expires_in" in result:
                result["expires_at"] = int(time.time()) + int(result["expires_in"]) - 60
            return result

    def _bearer_get(base_url: str, path: str, token: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """GET request with bearer authentication"""
        url = f"{base_url.rstrip('/')}{path if path.startswith('/') else '/' + path}"
        headers = {"authorization": f"Bearer {token}", "user-agent": USER_AGENT}
        with httpx.Client(timeout=DEFAULT_TIMEOUT) as client:
            resp = client.get(url, headers=headers, params=params or {})
            resp.raise_for_status()
            return resp.json()

    def _bearer_post(base_url: str, path: str, token: str, json_body: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """POST request with bearer authentication"""
        url = f"{base_url.rstrip('/')}{path if path.startswith('/') else '/' + path}"
        headers = {"authorization": f"Bearer {token}", "user-agent": USER_AGENT, "content-type": "application/json"}
        with httpx.Client(timeout=DEFAULT_TIMEOUT) as client:
            resp = client.post(url, headers=headers, json=json_body or {})
            resp.raise_for_status()
            return resp.json()

    # ========== OAuth Authentication Tools ==========

    @server.tool()
    def tab_oauth_password_grant(
        ctx: Context,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Obtain access and refresh tokens via password grant (for personal account betting)"""
        cfg: ConfigSchema = ctx.session_config
        data = {
            "grant_type": "password",
            "client_id": client_id or cfg.client_id,
            "client_secret": client_secret or cfg.client_secret,
            "username": username or cfg.username,
            "password": password or cfg.password,
        }
        if not all([data["client_id"], data["client_secret"], data["username"], data["password"]]):
            raise ValueError("Missing required OAuth credentials")
        return _oauth_post(cfg.base_url, data)

    @server.tool()
    def tab_oauth_refresh(
        ctx: Context,
        refresh_token: Optional[str] = None,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Refresh access token using refresh_token grant"""
        cfg: ConfigSchema = ctx.session_config
        data = {
            "grant_type": "refresh_token",
            "client_id": client_id or cfg.client_id,
            "client_secret": client_secret or cfg.client_secret,
            "refresh_token": refresh_token or cfg.refresh_token,
        }
        if not all([data["client_id"], data["client_secret"], data["refresh_token"]]):
            raise ValueError("Missing required OAuth credentials")
        return _oauth_post(cfg.base_url, data)

    @server.tool()
    def tab_oauth_client_credentials(
        ctx: Context,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Obtain token via client_credentials grant (for public data, no account needed)"""
        cfg: ConfigSchema = ctx.session_config
        data = {
            "grant_type": "client_credentials",
            "client_id": client_id or cfg.client_id,
            "client_secret": client_secret or cfg.client_secret,
        }
        if not all([data["client_id"], data["client_secret"]]):
            raise ValueError("Missing required OAuth credentials")
        return _oauth_post(cfg.base_url, data)

    # ========== Racing Endpoints ==========

    @server.tool()
    def racing_get_all_meeting_dates(
        ctx: Context,
        access_token: str,
        jurisdiction: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get all available racing meeting dates"""
        cfg: ConfigSchema = ctx.session_config
        params = {"jurisdiction": jurisdiction or cfg.jurisdiction}
        return _bearer_get(cfg.base_url, "/v1/tab-info-service/racing/dates", access_token, params)

    @server.tool()
    def racing_get_meetings(
        ctx: Context,
        access_token: str,
        meeting_date: str,
        jurisdiction: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get all meetings for a specific date (YYYY-MM-DD)"""
        cfg: ConfigSchema = ctx.session_config
        params = {"jurisdiction": jurisdiction or cfg.jurisdiction}
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
        """Get all races in a meeting. race_type: R(Racing), H(Harness), G(Greyhounds)"""
        cfg: ConfigSchema = ctx.session_config
        params = {"jurisdiction": jurisdiction or cfg.jurisdiction}
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
        """Get detailed information for a specific race"""
        cfg: ConfigSchema = ctx.session_config
        params = {"jurisdiction": jurisdiction or cfg.jurisdiction, "fixedOdds": str(fixed_odds).lower()}
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
        """Get next-to-go races ordered by start time"""
        cfg: ConfigSchema = ctx.session_config
        params: Dict[str, Any] = {"jurisdiction": jurisdiction or cfg.jurisdiction}
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
        """Get form guide for a race"""
        cfg: ConfigSchema = ctx.session_config
        params = {"jurisdiction": jurisdiction or cfg.jurisdiction}
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
        """Get form guide for a specific runner"""
        cfg: ConfigSchema = ctx.session_config
        params = {"jurisdiction": jurisdiction or cfg.jurisdiction}
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
        """Get pool approximates for a race. wagering_product: WIN, PLACE, QUINELLA, EXACTA, etc."""
        cfg: ConfigSchema = ctx.session_config
        params = {"jurisdiction": jurisdiction or cfg.jurisdiction}
        path = f"/v1/tab-info-service/racing/dates/{meeting_date}/meetings/{race_type}/{venue_mnemonic}/races/{race_number}/pools/{wagering_product}/approximates"
        return _bearer_get(cfg.base_url, path, access_token, params)

    @server.tool()
    def racing_get_open_jackpots(
        ctx: Context,
        access_token: str,
        jurisdiction: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get all currently open jackpots"""
        cfg: ConfigSchema = ctx.session_config
        params = {"jurisdiction": jurisdiction or cfg.jurisdiction}
        return _bearer_get(cfg.base_url, "/v1/tab-info-service/racing/jackpots", access_token, params)

    @server.tool()
    def racing_get_jackpot_pools(
        ctx: Context,
        access_token: str,
        meeting_date: str,
        jurisdiction: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get jackpot pools for a specific date"""
        cfg: ConfigSchema = ctx.session_config
        params = {"jurisdiction": jurisdiction or cfg.jurisdiction}
        return _bearer_get(cfg.base_url, f"/v1/tab-info-service/racing/dates/{meeting_date}/jackpot-pools", access_token, params)

    # ========== Sports Endpoints ==========

    @server.tool()
    def sports_get_all_open(
        ctx: Context,
        access_token: str,
        jurisdiction: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get all sports with at least one open or suspended market"""
        cfg: ConfigSchema = ctx.session_config
        params = {"jurisdiction": jurisdiction or cfg.jurisdiction}
        return _bearer_get(cfg.base_url, "/v1/tab-info-service/sports", access_token, params)

    @server.tool()
    def sports_get_open_sport(
        ctx: Context,
        access_token: str,
        sport_name: str,
        jurisdiction: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get a specific sport with open markets (e.g., 'Basketball', 'Rugby League')"""
        cfg: ConfigSchema = ctx.session_config
        params = {"jurisdiction": jurisdiction or cfg.jurisdiction}
        return _bearer_get(cfg.base_url, f"/v1/tab-info-service/sports/{sport_name}", access_token, params)

    @server.tool()
    def sports_get_open_competition(
        ctx: Context,
        access_token: str,
        sport_name: str,
        competition_name: str,
        jurisdiction: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get a specific competition with open markets (e.g., sport='Basketball', competition='NBA')"""
        cfg: ConfigSchema = ctx.session_config
        params = {"jurisdiction": jurisdiction or cfg.jurisdiction}
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
        """Get a specific tournament with open markets"""
        cfg: ConfigSchema = ctx.session_config
        params = {"jurisdiction": jurisdiction or cfg.jurisdiction}
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
        """Get a specific match in a competition with open markets"""
        cfg: ConfigSchema = ctx.session_config
        params = {"jurisdiction": jurisdiction or cfg.jurisdiction}
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
        """Get a specific match in a tournament with open markets"""
        cfg: ConfigSchema = ctx.session_config
        params = {"jurisdiction": jurisdiction or cfg.jurisdiction}
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
        """Get next-to-go sports matches sorted by start time"""
        cfg: ConfigSchema = ctx.session_config
        params: Dict[str, Any] = {"jurisdiction": jurisdiction or cfg.jurisdiction}
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
        """Get all sports with at least one resulted market"""
        cfg: ConfigSchema = ctx.session_config
        params = {"jurisdiction": jurisdiction or cfg.jurisdiction}
        return _bearer_get(cfg.base_url, "/v1/tab-info-service/sports/results", access_token, params)

    @server.tool()
    def sports_get_resulted_sport(
        ctx: Context,
        access_token: str,
        sport_name: str,
        jurisdiction: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get a specific sport with resulted markets"""
        cfg: ConfigSchema = ctx.session_config
        params = {"jurisdiction": jurisdiction or cfg.jurisdiction}
        return _bearer_get(cfg.base_url, f"/v1/tab-info-service/sports/results/{sport_name}", access_token, params)

    @server.tool()
    def sports_get_resulted_competition(
        ctx: Context,
        access_token: str,
        sport_name: str,
        competition_name: str,
        jurisdiction: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get a specific competition with resulted markets"""
        cfg: ConfigSchema = ctx.session_config
        params = {"jurisdiction": jurisdiction or cfg.jurisdiction}
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
        """Get a specific match with results in a competition"""
        cfg: ConfigSchema = ctx.session_config
        params = {"jurisdiction": jurisdiction or cfg.jurisdiction}
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
        """Get all FootyTAB rounds for a sport (e.g., 'AFL', 'Rugby League')"""
        cfg: ConfigSchema = ctx.session_config
        params = {"jurisdiction": jurisdiction or cfg.jurisdiction}
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
        """Get FootyTAB round details for a specific round number"""
        cfg: ConfigSchema = ctx.session_config
        params: Dict[str, Any] = {"jurisdiction": jurisdiction or cfg.jurisdiction}
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
        """Generic GET request to any Tabcorp API endpoint with bearer authentication"""
        cfg: ConfigSchema = ctx.session_config
        p = dict(params or {})
        if "jurisdiction" not in p and jurisdiction:
            p["jurisdiction"] = jurisdiction or cfg.jurisdiction
        return _bearer_get(cfg.base_url, path, access_token, p)

    @server.tool()
    def tab_post(
        ctx: Context,
        access_token: str,
        path: str,
        body: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Generic POST request to any Tabcorp API endpoint with bearer authentication"""
        cfg: ConfigSchema = ctx.session_config
        return _bearer_post(cfg.base_url, path, access_token, body or {})

    return server
