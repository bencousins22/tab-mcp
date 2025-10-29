"""
Smithery MCP server: Tabcorp OAuth (password grant + refresh) and querying tools
- Configure session with your credentials if desired (client_id/secret, username, password, jurisdiction)
- Use tools to obtain access/refresh tokens and make API requests
"""
from __future__ import annotations

import time
from typing import Any, Dict, Optional

import httpx
from mcp.server.fastmcp import Context, FastMCP
from pydantic import BaseModel, Field
from smithery.decorators import smithery


TAB_BASE_URL_DEFAULT = "https://api.beta.tab.com.au"
OAUTH_TOKEN_PATH = "/oauth/token"
USER_AGENT = "tab-mcp/0.1 (+smithery)"


class ConfigSchema(BaseModel):
    client_id: Optional[str] = Field(None, description="Tabcorp OAuth client_id")
    client_secret: Optional[str] = Field(None, description="Tabcorp OAuth client_secret")
    username: Optional[str] = Field(None, description="TAB account number (for password grant)")
    password: Optional[str] = Field(None, description="TAB account password (for password grant)")
    refresh_token: Optional[str] = Field(None, description="Optional cached refresh token")
    jurisdiction: str = Field("NSW", description="Jurisdiction code, e.g., NSW, VIC")
    base_url: str = Field(TAB_BASE_URL_DEFAULT, description="Tabcorp API base URL")
    auto_refresh: bool = Field(True, description="Whether client should refresh tokens when close to expiry")


@smithery.server(config_schema=ConfigSchema)
def create_server() -> FastMCP:
    server = FastMCP("Tabcorp API Server")

    def _oauth_post(base_url: str, data: Dict[str, str]) -> Dict[str, Any]:
        url = base_url.rstrip("/") + OAUTH_TOKEN_PATH
        headers = {"content-type": "application/x-www-form-urlencoded", "user-agent": USER_AGENT}
        with httpx.Client(timeout=30.0) as client:
            resp = client.post(url, data=data, headers=headers)
            try:
                resp.raise_for_status()
            except httpx.HTTPStatusError as e:
                # Attempt to parse JSON error
                err: Dict[str, Any]
                try:
                    err = resp.json()
                except Exception:
                    err = {"error": resp.text}
                raise ValueError(
                    f"OAuth request failed with status {resp.status_code}: {err}"
                ) from e
            try:
                return resp.json()
            except Exception as e:
                raise ValueError("OAuth response is not valid JSON") from e

    def _bearer_get(base_url: str, path: str, token: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        url = base_url.rstrip("/") + (path if path.startswith("/") else f"/{path}")
        headers = {"authorization": f"Bearer {token}", "user-agent": USER_AGENT}
        with httpx.Client(timeout=30.0) as client:
            resp = client.get(url, headers=headers, params=params or {})
            try:
                resp.raise_for_status()
            except httpx.HTTPStatusError as e:
                try:
                    err = resp.json()
                except Exception:
                    err = {"error": resp.text}
                raise ValueError(
                    f"GET {path} failed with status {resp.status_code}: {err}"
                ) from e
            try:
                return resp.json()
            except Exception as e:
                raise ValueError("GET response is not valid JSON") from e

    def _bearer_post(base_url: str, path: str, token: str, json_body: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        url = base_url.rstrip("/") + (path if path.startswith("/") else f"/{path}")
        headers = {"authorization": f"Bearer {token}", "user-agent": USER_AGENT, "content-type": "application/json"}
        with httpx.Client(timeout=30.0) as client:
            resp = client.post(url, headers=headers, json=json_body or {})
            try:
                resp.raise_for_status()
            except httpx.HTTPStatusError as e:
                try:
                    err = resp.json()
                except Exception:
                    err = {"error": resp.text}
                raise ValueError(
                    f"POST {path} failed with status {resp.status_code}: {err}"
                ) from e
            try:
                return resp.json()
            except Exception as e:
                raise ValueError("POST response is not valid JSON") from e

    # Tools

    @server.tool()
    def tab_oauth_password_grant(
        ctx: Context,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        base_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Obtain bearer access_token and refresh_token via password grant.
        Pulls missing values from session config when not provided explicitly.
        """
        cfg: ConfigSchema = ctx.session_config
        cid = client_id or cfg.client_id
        csec = client_secret or cfg.client_secret
        user = username or cfg.username
        pwd = password or cfg.password
        burl = base_url or cfg.base_url or TAB_BASE_URL_DEFAULT

        if not all([cid, csec, user, pwd]):
            missing = [name for name, val in [
                ("client_id", cid), ("client_secret", csec), ("username", user), ("password", pwd)
            ] if not val]
            raise ValueError(f"Missing required fields for password grant: {', '.join(missing)}")

        data = {
            "grant_type": "password",
            "client_id": cid,
            "client_secret": csec,
            "username": user,
            "password": pwd,
        }
        out = _oauth_post(burl, data)
        # Add expires_at convenience timestamp (buffer 60s)
        expires_in = int(out.get("expires_in", 0) or 0)
        out["expires_at"] = int(time.time()) + max(0, expires_in - 60)
        out["base_url"] = burl
        return out

    @server.tool()
    def tab_oauth_refresh(
        ctx: Context,
        refresh_token: Optional[str] = None,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        base_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Refresh access token using refresh_token flow. Missing values are sourced from session config."""
        cfg: ConfigSchema = ctx.session_config
        rtok = refresh_token or cfg.refresh_token
        cid = client_id or cfg.client_id
        csec = client_secret or cfg.client_secret
        burl = base_url or cfg.base_url or TAB_BASE_URL_DEFAULT

        if not all([cid, csec, rtok]):
            missing = [name for name, val in [("client_id", cid), ("client_secret", csec), ("refresh_token", rtok)] if not val]
            raise ValueError(f"Missing required fields for refresh_token grant: {', '.join(missing)}")

        data = {
            "grant_type": "refresh_token",
            "client_id": cid,
            "client_secret": csec,
            "refresh_token": rtok,
        }
        out = _oauth_post(burl, data)
        expires_in = int(out.get("expires_in", 0) or 0)
        out["expires_at"] = int(time.time()) + max(0, expires_in - 60)
        out["base_url"] = burl
        return out

    @server.tool()
    def tab_oauth_client_credentials(
        ctx: Context,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        base_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Obtain token using client_credentials grant (for non-account queries)."""
        cfg: ConfigSchema = ctx.session_config
        cid = client_id or cfg.client_id
        csec = client_secret or cfg.client_secret
        burl = base_url or cfg.base_url or TAB_BASE_URL_DEFAULT

        if not all([cid, csec]):
            missing = [name for name, val in [("client_id", cid), ("client_secret", csec)] if not val]
            raise ValueError(f"Missing required fields for client_credentials: {', '.join(missing)}")

        data = {
            "grant_type": "client_credentials",
            "client_id": cid,
            "client_secret": csec,
        }
        out = _oauth_post(burl, data)
        expires_in = int(out.get("expires_in", 0) or 0)
        out["expires_at"] = int(time.time()) + max(0, expires_in - 60)
        out["base_url"] = burl
        return out

    @server.tool()
    def tab_get(
        ctx: Context,
        access_token: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        jurisdiction: Optional[str] = None,
        base_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generic GET helper with Bearer token.
        path: e.g., "/v1/tab-info-service/sports" or "v1/tab-info-service/sports"
        params: dict of query parameters; jurisdiction defaults from session config if not provided
        """
        cfg: ConfigSchema = ctx.session_config
        burl = base_url or cfg.base_url or TAB_BASE_URL_DEFAULT
        j = jurisdiction or cfg.jurisdiction or "NSW"
        p = dict(params or {})
        # include jurisdiction if not explicitly provided
        if "jurisdiction" not in p:
            p["jurisdiction"] = j
        return _bearer_get(burl, path, access_token, p)

    @server.tool()
    def tab_post(
        ctx: Context,
        access_token: str,
        path: str,
        body: Optional[Dict[str, Any]] = None,
        base_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generic POST helper with Bearer token for endpoints like placing bets."""
        cfg: ConfigSchema = ctx.session_config
        burl = base_url or cfg.base_url or TAB_BASE_URL_DEFAULT
        return _bearer_post(burl, path, access_token, body or {})

    @server.tool()
    def tab_list_sports(
        ctx: Context,
        access_token: str,
        jurisdiction: Optional[str] = None,
        base_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Convenience wrapper for GET /v1/tab-info-service/sports?jurisdiction=..."""
        cfg: ConfigSchema = ctx.session_config
        burl = base_url or cfg.base_url or TAB_BASE_URL_DEFAULT
        j = jurisdiction or cfg.jurisdiction or "NSW"
        return _bearer_get(burl, "/v1/tab-info-service/sports", access_token, {"jurisdiction": j})

    # Keep a simple hello tool for sanity checks
    @server.tool()
    def hello(ctx: Context, name: str) -> str:
        cfg: ConfigSchema = ctx.session_config
        return f"Hello, {name}! (jurisdiction={cfg.jurisdiction})"

    return server
