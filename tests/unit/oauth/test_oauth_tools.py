"""Unit tests for OAuth authentication tools"""
import pytest
import time
from unittest.mock import Mock
import respx
from httpx import Response

from tab_mcp.server import (
    create_server,
    TabcorpAPIError,
    TAB_BASE_URL,
    OAUTH_TOKEN_PATH
)


@pytest.mark.unit
@pytest.mark.oauth
class TestOAuthPasswordGrant:
    """Test password grant OAuth flow"""

    def test_password_grant_success(self, mock_context, respx_mock, valid_oauth_response):
        """Test successful password grant authentication"""
        # Mock OAuth endpoint
        route = respx_mock.post(f"{TAB_BASE_URL}{OAUTH_TOKEN_PATH}")
        route.return_value = Response(200, json=valid_oauth_response)

        # Create server and call tool
        server = create_server()
        result = server.tool_manager.tools["tab_oauth_password_grant"].fn(
            mock_context,
            client_id="test_client",
            client_secret="test_secret",
            username="test_user",
            password="test_pass"
        )

        # Verify request was made
        assert route.called
        request = route.calls[0].request
        assert request.method == "POST"
        assert "application/x-www-form-urlencoded" in request.headers["content-type"]

        # Verify response
        assert result["access_token"] == "test_access_token_12345"
        assert result["refresh_token"] == "test_refresh_token_67890"
        assert result["token_type"] == "Bearer"
        assert result["expires_in"] == 3600
        assert "expires_at" in result
        assert result["expires_at"] > time.time()

    def test_password_grant_from_config(self, mock_context, respx_mock, valid_oauth_response):
        """Test password grant using credentials from config"""
        # Configure mock context with credentials
        mock_context.session_config.client_id = "config_client"
        mock_context.session_config.client_secret = "config_secret"
        mock_context.session_config.username = "config_user"
        mock_context.session_config.password = "config_pass"

        # Mock OAuth endpoint
        route = respx_mock.post(f"{TAB_BASE_URL}{OAUTH_TOKEN_PATH}")
        route.return_value = Response(200, json=valid_oauth_response)

        # Call without explicit credentials
        server = create_server()
        result = server.tool_manager.tools["tab_oauth_password_grant"].fn(mock_context)

        # Verify it used config credentials
        assert route.called
        assert result["access_token"] == "test_access_token_12345"

    def test_password_grant_missing_credentials(self, mock_context):
        """Test password grant with missing credentials raises error"""
        # Clear config credentials
        mock_context.session_config.client_id = None
        mock_context.session_config.client_secret = None

        server = create_server()
        with pytest.raises(ValueError, match="Missing required credentials"):
            server.tool_manager.tools["tab_oauth_password_grant"].fn(mock_context)

    def test_password_grant_invalid_credentials(self, mock_context, respx_mock, oauth_error_response):
        """Test password grant with invalid credentials"""
        # Mock OAuth error
        route = respx_mock.post(f"{TAB_BASE_URL}{OAUTH_TOKEN_PATH}")
        route.return_value = Response(401, json=oauth_error_response)

        server = create_server()
        with pytest.raises(TabcorpAPIError) as exc_info:
            server.tool_manager.tools["tab_oauth_password_grant"].fn(
                mock_context,
                client_id="bad_client",
                client_secret="bad_secret",
                username="bad_user",
                password="bad_pass"
            )

        assert exc_info.value.status_code == 401
        assert "invalid" in str(exc_info.value).lower()


@pytest.mark.unit
@pytest.mark.oauth
class TestOAuthRefresh:
    """Test refresh token OAuth flow"""

    def test_refresh_token_success(self, mock_context, respx_mock, valid_oauth_response):
        """Test successful token refresh"""
        # Mock OAuth endpoint
        route = respx_mock.post(f"{TAB_BASE_URL}{OAUTH_TOKEN_PATH}")
        route.return_value = Response(200, json=valid_oauth_response)

        server = create_server()
        result = server.tool_manager.tools["tab_oauth_refresh"].fn(
            mock_context,
            refresh_token="old_refresh_token",
            client_id="test_client",
            client_secret="test_secret"
        )

        # Verify request
        assert route.called
        request_body = route.calls[0].request.content.decode()
        assert "grant_type=refresh_token" in request_body
        assert "old_refresh_token" in request_body

        # Verify response
        assert result["access_token"] == "test_access_token_12345"
        assert result["refresh_token"] == "test_refresh_token_67890"


@pytest.mark.unit
@pytest.mark.oauth  
class TestOAuthClientCredentials:
    """Test client credentials OAuth flow"""

    def test_client_credentials_success(self, mock_context, respx_mock):
        """Test successful client credentials authentication"""
        # Mock response (no refresh_token for client_credentials)
        response = {
            "access_token": "client_creds_token",
            "token_type": "Bearer",
            "expires_in": 3600,
            "expires_at": int(time.time()) + 3540
        }
        
        route = respx_mock.post(f"{TAB_BASE_URL}{OAUTH_TOKEN_PATH}")
        route.return_value = Response(200, json=response)

        server = create_server()
        result = server.tool_manager.tools["tab_oauth_client_credentials"].fn(
            mock_context,
            client_id="test_client",
            client_secret="test_secret"
        )

        # Verify request
        assert route.called
        request_body = route.calls[0].request.content.decode()
        assert "grant_type=client_credentials" in request_body

        # Verify response
        assert result["access_token"] == "client_creds_token"
        assert "refresh_token" not in result  # Not provided for client_credentials
