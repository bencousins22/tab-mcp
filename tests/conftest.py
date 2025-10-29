"""Shared pytest fixtures and utilities for Tabcorp MCP Server tests"""
import os
import time
from typing import Dict, Any, Optional
from unittest.mock import Mock

import pytest
import respx
from httpx import Response
from mcp.server.fastmcp import Context

# Test configuration
TEST_BASE_URL = "https://api.beta.tab.com.au"
TEST_CLIENT_ID = os.getenv("TAB_CLIENT_ID", "test_client_id")
TEST_CLIENT_SECRET = os.getenv("TAB_CLIENT_SECRET", "test_client_secret")
TEST_USERNAME = os.getenv("TAB_USERNAME", "test_username")
TEST_PASSWORD = os.getenv("TAB_PASSWORD", "test_password")


# ========== Configuration Fixtures ==========

@pytest.fixture
def test_config():
    """Provide test configuration matching ConfigSchema"""
    from tab_mcp.server import ConfigSchema
    return ConfigSchema(
        client_id=TEST_CLIENT_ID,
        client_secret=TEST_CLIENT_SECRET,
        username=TEST_USERNAME,
        password=TEST_PASSWORD,
        jurisdiction="NSW",
        base_url=TEST_BASE_URL
    )


@pytest.fixture
def mock_context(test_config):
    """Provide mock MCP Context with test configuration"""
    ctx = Mock(spec=Context)
    ctx.session_config = test_config
    return ctx


# ========== OAuth Response Fixtures ==========

@pytest.fixture
def valid_oauth_response():
    """Valid OAuth token response"""
    return {
        "access_token": "test_access_token_12345",
        "refresh_token": "test_refresh_token_67890",
        "token_type": "Bearer",
        "expires_in": 3600,
        "expires_at": int(time.time()) + 3540  # 59 minutes from now
    }


@pytest.fixture
def expired_oauth_response():
    """Expired OAuth token response"""
    return {
        "access_token": "expired_token",
        "refresh_token": "expired_refresh",
        "token_type": "Bearer",
        "expires_in": 0,
        "expires_at": int(time.time()) - 100  # Already expired
    }


@pytest.fixture
def oauth_error_response():
    """OAuth error response"""
    return {
        "error": "invalid_grant",
        "error_description": "The provided credentials are invalid"
    }


# ========== Racing Data Fixtures ==========

@pytest.fixture
def sample_race_meeting():
    """Sample race meeting data"""
    return {
        "meetings": [
            {
                "meetingDate": "2025-10-29",
                "location": "Randwick",
                "venueMnemonic": "RAN",
                "meetingName": "Randwick",
                "raceType": "R",
                "meetingStatus": "OPEN",
                "races": [
                    {
                        "raceNumber": 1,
                        "raceName": "Race 1",
                        "raceStartTime": "2025-10-29T12:00:00Z",
                        "raceStatus": "OPEN"
                    }
                ]
            }
        ]
    }


@pytest.fixture
def sample_race_details():
    """Sample detailed race data"""
    return {
        "raceNumber": 1,
        "raceName": "Maiden Handicap",
        "raceDistance": 1200,
        "raceStartTime": "2025-10-29T12:00:00Z",
        "runners": [
            {
                "runnerNumber": "1",
                "runnerName": "Fast Horse",
                "barrier": 1,
                "fixedOdds": {
                    "returnWin": 3.50,
                    "returnPlace": 1.80
                }
            },
            {
                "runnerNumber": "2",
                "runnerName": "Quick Runner",
                "barrier": 2,
                "fixedOdds": {
                    "returnWin": 5.00,
                    "returnPlace": 2.10
                }
            }
        ]
    }


@pytest.fixture
def sample_next_to_go():
    """Sample next-to-go races"""
    return {
        "races": [
            {
                "meetingDate": "2025-10-29",
                "venueMnemonic": "RAN",
                "raceType": "R",
                "raceNumber": 1,
                "raceStartTime": "2025-10-29T12:00:00Z",
                "secondsToJump": 300
            },
            {
                "meetingDate": "2025-10-29",
                "venueMnemonic": "FLE",
                "raceType": "R",
                "raceNumber": 2,
                "raceStartTime": "2025-10-29T12:30:00Z",
                "secondsToJump": 1800
            }
        ]
    }


# ========== Sports Data Fixtures ==========

@pytest.fixture
def sample_sports_list():
    """Sample sports list"""
    return {
        "sports": [
            {
                "sportName": "Basketball",
                "competitions": [
                    {"competitionName": "NBA"},
                    {"competitionName": "NBL"}
                ]
            },
            {
                "sportName": "Rugby League",
                "competitions": [
                    {"competitionName": "NRL"}
                ]
            }
        ]
    }


@pytest.fixture
def sample_sport_competition():
    """Sample sport competition with matches"""
    return {
        "competitionName": "NBA",
        "matches": [
            {
                "matchName": "Lakers v Warriors",
                "startTime": "2025-10-30T02:00:00Z",
                "competitors": [
                    {"name": "Lakers", "position": "HOME"},
                    {"name": "Warriors", "position": "AWAY"}
                ],
                "markets": [
                    {
                        "marketName": "Head To Head",
                        "propositions": [
                            {"name": "Lakers", "returnWin": 1.85},
                            {"name": "Warriors", "returnWin": 2.00}
                        ]
                    }
                ]
            }
        ]
    }


# ========== Mock HTTP Fixtures ==========

@pytest.fixture
def respx_mock():
    """Enable respx HTTP mocking"""
    with respx.mock:
        yield respx


@pytest.fixture
def mock_oauth_success(respx_mock, valid_oauth_response):
    """Mock successful OAuth token request"""
    route = respx_mock.post(f"{TEST_BASE_URL}/oauth/token")
    route.return_value = Response(200, json=valid_oauth_response)
    return route


@pytest.fixture
def mock_oauth_failure(respx_mock, oauth_error_response):
    """Mock failed OAuth token request"""
    route = respx_mock.post(f"{TEST_BASE_URL}/oauth/token")
    route.return_value = Response(401, json=oauth_error_response)
    return route


@pytest.fixture
def mock_racing_dates_success(respx_mock):
    """Mock successful racing dates request"""
    response_data = {
        "dates": [
            {"date": "2025-10-29", "meetingCount": 15},
            {"date": "2025-10-30", "meetingCount": 12}
        ]
    }
    route = respx_mock.get(f"{TEST_BASE_URL}/v1/tab-info-service/racing/dates")
    route.return_value = Response(200, json=response_data)
    return route


@pytest.fixture
def mock_api_error(respx_mock):
    """Mock API error response"""
    error_data = {
        "error": {
            "message": "Internal server error",
            "code": "INTERNAL_ERROR"
        }
    }
    route = respx_mock.get(f"{TEST_BASE_URL}/v1/tab-info-service/racing/dates")
    route.return_value = Response(500, json=error_data)
    return route


# ========== Helper Functions ==========

def create_mock_response(status_code: int, json_data: Optional[Dict[str, Any]] = None) -> Response:
    """Create a mock HTTP response"""
    return Response(status_code, json=json_data or {})


def assert_valid_oauth_token(token_data: Dict[str, Any]):
    """Assert OAuth token response has required fields"""
    assert "access_token" in token_data
    assert "token_type" in token_data
    assert token_data["token_type"] == "Bearer"
    if "expires_in" in token_data:
        assert token_data["expires_in"] > 0
        assert "expires_at" in token_data


def assert_tabcorp_error(error, expected_message: Optional[str] = None, expected_status: Optional[int] = None):
    """Assert TabcorpAPIError has expected properties"""
    from tab_mcp.server import TabcorpAPIError
    assert isinstance(error, TabcorpAPIError)
    if expected_message:
        assert expected_message in str(error)
    if expected_status:
        assert error.status_code == expected_status
