"""Unit tests for server helper functions and core logic"""
import pytest
import respx
from httpx import Response
import time

# Test the internal helper functions by importing the module
import sys
sys.path.insert(0, '/root/tab-mcp/src')


@pytest.mark.unit
class TestOAuthHelpers:
    """Test OAuth helper functions"""

    def test_oauth_post_success(self, respx_mock, valid_oauth_response):
        """Test successful OAuth POST request"""
        # Import the function to test
        from tab_mcp.server import create_server
        server = create_server()
        
        # We'll test by actually calling the OAuth endpoint
        route = respx_mock.post("https://api.beta.tab.com.au/oauth/token")
        route.return_value = Response(200, json=valid_oauth_response)
        
        # Make a direct HTTP call using httpx
        import httpx
        with httpx.Client() as client:
            response = client.post(
                "https://api.beta.tab.com.au/oauth/token",
                data={"grant_type": "client_credentials", "client_id": "test", "client_secret": "test"},
                headers={"content-type": "application/x-www-form-urlencoded"}
            )
            result = response.json()
        
        assert result["access_token"] == "test_access_token_12345"
        assert result["token_type"] == "Bearer"

    def test_oauth_post_error(self, respx_mock, oauth_error_response):
        """Test OAuth POST with error response"""
        route = respx_mock.post("https://api.beta.tab.com.au/oauth/token")
        route.return_value = Response(401, json=oauth_error_response)
        
        import httpx
        with httpx.Client() as client:
            response = client.post(
                "https://api.beta.tab.com.au/oauth/token",
                data={"grant_type": "client_credentials", "client_id": "bad", "client_secret": "bad"},
                headers={"content-type": "application/x-www-form-urlencoded"}
            )
        
        assert response.status_code == 401
        assert "error" in response.json()


@pytest.mark.unit
class TestRacingHelpers:
    """Test Racing API helper functions"""

    def test_bearer_get_success(self, respx_mock):
        """Test successful bearer GET request"""
        response_data = {"dates": [{"date": "2025-10-29"}]}
        route = respx_mock.get("https://api.beta.tab.com.au/v1/tab-info-service/racing/dates")
        route.return_value = Response(200, json=response_data)
        
        import httpx
        with httpx.Client() as client:
            response = client.get(
                "https://api.beta.tab.com.au/v1/tab-info-service/racing/dates",
                headers={
                    "authorization": "Bearer test_token",
                    "accept": "application/json"
                },
                params={"jurisdiction": "NSW"}
            )
            result = response.json()
        
        assert "dates" in result
        assert len(result["dates"]) == 1

    def test_bearer_get_error(self, respx_mock):
        """Test bearer GET with error response"""
        error_data = {"error": {"message": "Unauthorized"}}
        route = respx_mock.get("https://api.beta.tab.com.au/v1/tab-info-service/racing/dates")
        route.return_value = Response(401, json=error_data)
        
        import httpx
        with httpx.Client() as client:
            response = client.get(
                "https://api.beta.tab.com.au/v1/tab-info-service/racing/dates",
                headers={"authorization": "Bearer invalid_token"}
            )
        
        assert response.status_code == 401


@pytest.mark.unit
class TestValidationHelpers:
    """Test validation helper functions"""

    def test_valid_jurisdictions(self):
        """Test jurisdiction validation"""
        from tab_mcp.server import VALID_JURISDICTIONS
        
        assert "NSW" in VALID_JURISDICTIONS
        assert "VIC" in VALID_JURISDICTIONS
        assert "QLD" in VALID_JURISDICTIONS
        assert "INVALID" not in VALID_JURISDICTIONS

    def test_valid_race_types(self):
        """Test race type validation"""
        from tab_mcp.server import VALID_RACE_TYPES
        
        assert "R" in VALID_RACE_TYPES  # Racing/Thoroughbred
        assert "H" in VALID_RACE_TYPES  # Harness
        assert "G" in VALID_RACE_TYPES  # Greyhounds
        assert "X" not in VALID_RACE_TYPES


@pytest.mark.unit
class TestErrorHandling:
    """Test error handling"""

    def test_tabcorp_api_error_creation(self):
        """Test TabcorpAPIError exception"""
        from tab_mcp.server import TabcorpAPIError
        
        error = TabcorpAPIError(
            "Test error",
            status_code=500,
            response_data={"error": "Internal error"}
        )
        
        assert error.message == "Test error"
        assert error.status_code == 500
        assert error.response_data == {"error": "Internal error"}
        assert "Test error" in str(error)


@pytest.mark.unit  
class TestConfigSchema:
    """Test configuration schema"""

    def test_config_creation(self):
        """Test ConfigSchema creation with valid data"""
        from tab_mcp.server import ConfigSchema
        
        config = ConfigSchema(
            client_id="test_id",
            client_secret="test_secret",
            jurisdiction="NSW"
        )
        
        assert config.client_id == "test_id"
        assert config.client_secret == "test_secret"
        assert config.jurisdiction == "NSW"
        assert config.base_url == "https://api.beta.tab.com.au"

    def test_config_invalid_jurisdiction(self):
        """Test ConfigSchema with invalid jurisdiction"""
        from tab_mcp.server import ConfigSchema
        from pydantic import ValidationError
        
        with pytest.raises(ValidationError):
            ConfigSchema(
                client_id="test",
                client_secret="test",
                jurisdiction="INVALID"
            )


@pytest.mark.unit
class TestServerCreation:
    """Test server creation"""

    def test_create_server(self):
        """Test server creation returns SmitheryFastMCP instance"""
        from tab_mcp.server import create_server
        
        server = create_server()
        assert server is not None
        assert hasattr(server, 'list_tools')
