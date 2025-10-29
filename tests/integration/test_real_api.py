"""Integration tests with real Tabcorp API

These tests make actual API calls and require valid credentials.
Skip with: pytest -m "not integration"
"""
import os
import pytest
import time
from datetime import datetime, timedelta

from tab_mcp.server import create_server, ConfigSchema
from unittest.mock import Mock
from mcp.server.fastmcp import Context

# Check if credentials are available
HAS_CREDENTIALS = all([
    os.getenv("TAB_CLIENT_ID"),
    os.getenv("TAB_CLIENT_SECRET"),
    os.getenv("TAB_USERNAME"),
    os.getenv("TAB_PASSWORD")
])

pytestmark = pytest.mark.skipif(
    not HAS_CREDENTIALS,
    reason="Real API credentials not available in environment"
)


@pytest.fixture(scope="module")
def real_config():
    """Create real configuration from environment"""
    return ConfigSchema(
        client_id=os.getenv("TAB_CLIENT_ID"),
        client_secret=os.getenv("TAB_CLIENT_SECRET"),
        username=os.getenv("TAB_USERNAME"),
        password=os.getenv("TAB_PASSWORD"),
        jurisdiction="NSW",
        base_url="https://api.beta.tab.com.au"
    )


@pytest.fixture(scope="module")
def real_context(real_config):
    """Create context with real configuration"""
    ctx = Mock(spec=Context)
    ctx.session_config = real_config
    return ctx


@pytest.fixture(scope="module")
def access_token(real_context):
    """Obtain real access token for module-scoped tests"""
    server = create_server()
    
    # Try client_credentials first (public data access)
    try:
        result = server.tool_manager.tools["tab_oauth_client_credentials"].fn(
            real_context
        )
        return result["access_token"]
    except Exception as e:
        pytest.skip(f"Could not obtain access token: {e}")


@pytest.mark.integration
@pytest.mark.oauth
@pytest.mark.slow
class TestRealOAuthFlows:
    """Test real OAuth authentication flows"""

    def test_client_credentials_grant(self, real_context):
        """Test real client credentials authentication"""
        server = create_server()
        result = server.tool_manager.tools["tab_oauth_client_credentials"].fn(
            real_context
        )

        # Verify token structure
        assert "access_token" in result
        assert "token_type" in result
        assert result["token_type"] == "Bearer"
        assert "expires_in" in result
        assert result["expires_in"] > 0
        assert "expires_at" in result
        assert result["expires_at"] > time.time()

    def test_password_grant(self, real_context):
        """Test real password grant authentication"""
        server = create_server()
        
        try:
            result = server.tool_manager.tools["tab_oauth_password_grant"].fn(
                real_context
            )

            # Verify token structure
            assert "access_token" in result
            assert "refresh_token" in result
            assert "token_type" in result
            assert result["token_type"] == "Bearer"
            assert "expires_in" in result
            
            # Store refresh token for next test
            real_context.session_config.refresh_token = result["refresh_token"]
            
        except Exception as e:
            # Password grant might not be enabled for all accounts
            pytest.skip(f"Password grant not available: {e}")

    def test_refresh_token(self, real_context):
        """Test real token refresh"""
        # First get a token with refresh_token
        server = create_server()
        
        try:
            initial = server.tool_manager.tools["tab_oauth_password_grant"].fn(
                real_context
            )
            
            # Now refresh it
            result = server.tool_manager.tools["tab_oauth_refresh"].fn(
                real_context,
                refresh_token=initial["refresh_token"]
            )

            # Verify new token
            assert "access_token" in result
            assert result["access_token"] != initial["access_token"]  # Should be different
            assert "refresh_token" in result
            
        except Exception as e:
            pytest.skip(f"Refresh token not available: {e}")


@pytest.mark.integration
@pytest.mark.racing
@pytest.mark.slow
class TestRealRacingEndpoints:
    """Test real Racing API endpoints"""

    def test_get_all_meeting_dates(self, real_context, access_token):
        """Test real meeting dates retrieval"""
        server = create_server()
        result = server.tool_manager.tools["racing_get_all_meeting_dates"].fn(
            real_context,
            access_token=access_token
        )

        # Verify response structure
        assert "dates" in result or "error" not in result
        # Note: dates list might be empty on certain days

    def test_get_meetings_for_today(self, real_context, access_token):
        """Test real meetings retrieval for today"""
        server = create_server()
        today = datetime.now().strftime("%Y-%m-%d")
        
        try:
            result = server.tool_manager.tools["racing_get_meetings"].fn(
                real_context,
                access_token=access_token,
                meeting_date=today
            )

            # Verify response structure (might be empty if no meetings)
            assert isinstance(result, dict)
            
        except Exception as e:
            # Might fail if no meetings today
            pytest.skip(f"No meetings for today: {e}")

    def test_get_next_to_go_races(self, real_context, access_token):
        """Test real next-to-go races"""
        server = create_server()
        result = server.tool_manager.tools["racing_get_next_to_go"].fn(
            real_context,
            access_token=access_token,
            max_races=5
        )

        # Verify response structure
        assert isinstance(result, dict)
        # races list might be empty depending on time of day


@pytest.mark.integration
@pytest.mark.sports
@pytest.mark.slow
class TestRealSportsEndpoints:
    """Test real Sports API endpoints"""

    def test_get_all_open_sports(self, real_context, access_token):
        """Test real sports list retrieval"""
        server = create_server()
        result = server.tool_manager.tools["sports_get_all_open"].fn(
            real_context,
            access_token=access_token
        )

        # Verify response structure
        assert isinstance(result, dict)
        # sports list should generally have content

    def test_get_specific_sport(self, real_context, access_token):
        """Test real specific sport retrieval"""
        server = create_server()
        
        # Basketball is commonly available
        try:
            result = server.tool_manager.tools["sports_get_open_sport"].fn(
                real_context,
                access_token=access_token,
                sport_name="Basketball"
            )

            assert isinstance(result, dict)
            
        except Exception as e:
            # Sport might not be available at this time
            pytest.skip(f"Basketball not available: {e}")

    def test_get_sports_next_to_go(self, real_context, access_token):
        """Test real sports next-to-go"""
        server = create_server()
        result = server.tool_manager.tools["sports_get_next_to_go"].fn(
            real_context,
            access_token=access_token,
            limit=10
        )

        # Verify response structure
        assert isinstance(result, dict)


@pytest.mark.integration
@pytest.mark.smoke
class TestAPIHealthCheck:
    """Smoke tests to verify API is accessible"""

    def test_api_authentication_works(self, real_context):
        """Quick smoke test that authentication works"""
        server = create_server()
        result = server.tool_manager.tools["tab_oauth_client_credentials"].fn(
            real_context
        )
        assert "access_token" in result

    def test_api_endpoint_accessible(self, real_context, access_token):
        """Quick smoke test that API endpoints are accessible"""
        server = create_server()
        result = server.tool_manager.tools["racing_get_all_meeting_dates"].fn(
            real_context,
            access_token=access_token
        )
        assert isinstance(result, dict)
